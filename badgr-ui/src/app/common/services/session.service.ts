import {Injectable} from '@angular/core';
import {UserCredential} from '../model/user-credential.type';
import {AppConfigService} from '../app-config.service';
import {MessageService} from './message.service';
import {BaseHttpApiService} from './base-http-api.service';
import {
	ExternalAuthProvider,
	SocialAccountProviderInfo,
	socialAccountProviderInfos
} from '../model/user-profile-api.model';
import {throwExpr} from '../util/throw-expr';
import {UpdatableSubject} from '../util/updatable-subject';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {NavigationService} from './navigation.service';
import { DomSanitizer } from "@angular/platform-browser";
import { OAuthManager } from "./oauth-manager.service";

export const TOKEN_STORAGE_KEY = "LoginService.token";
const EXPIRATION_DATE_STORAGE_KEY = "LoginService.tokenExpirationDate";
const DEFAULT_EXPIRATION_SECONDS = 24 * 60 * 60;

export interface AuthorizationToken {
	access_token: string;
	expires_in?: number;
	refresh_token?: string;
	scope?: string;
	token_typ?: string;
}

@Injectable()
export class SessionService {
	baseUrl: string;

	// ✅ CORREÇÃO: Usar configuração diretamente do config
	enabledExternalAuthProviders: ExternalAuthProvider[];

	private loggedInSubject = new UpdatableSubject<boolean>();
	get loggedin$() { return this.loggedInSubject.asObservable(); }

	constructor(
		private http: HttpClient,
		private configService: AppConfigService,
		private messageService: MessageService,
		private navService: NavigationService,
	) {
		this.baseUrl = this.configService.apiConfig.baseUrl;
		
		// ✅ CORREÇÃO: Usar config direto, sem chamadas de API
		this.enabledExternalAuthProviders = this.configService.featuresConfig.externalAuthProviders || [];
		
		console.log('🎯 Providers configurados:', this.enabledExternalAuthProviders);
	}

	login(credential: UserCredential, sessionOnlyStorage = false): Promise<AuthorizationToken> {
		const endpoint = this.baseUrl + '/o/token';
		const scope = "rw:profile rw:issuer rw:backpack";
		const client_id = "public";

		const payload = `grant_type=password&client_id=${encodeURIComponent(client_id)}&scope=${encodeURIComponent(scope)}&username=${encodeURIComponent(credential.username)}&password=${encodeURIComponent(credential.password)}`;

		const headers = new HttpHeaders()
			.append('Content-Type', 'application/x-www-form-urlencoded');

		this.messageService.incrementPendingRequestCount();

		return this.http
			.post<AuthorizationToken>(
				endpoint,
				payload,
				{
					observe: "response",
					responseType: "json",
					headers
				}
			)
			.toPromise()
			.then(r => BaseHttpApiService.addTestingDelay(r, this.configService))
			.finally(
				() => this.messageService.decrementPendingRequestCount()
			)
			.then(r => {
				if (r.status < 200 || r.status >= 300) {
					throw new Error("Login Failed: " + r.status);
				}

				this.storeToken(r.body, sessionOnlyStorage);
				return r.body;
			});
	}

	initiateUnauthenticatedExternalAuth(provider: ExternalAuthProvider) {
		console.log('🚀 Iniciando auth para:', provider);
		window.location.href = `${this.baseUrl}/account/sociallogin?provider=${encodeURIComponent(provider.slug)}`;
	}

	logout(nextObservable = true): void {
		localStorage.removeItem(TOKEN_STORAGE_KEY);
		sessionStorage.removeItem(TOKEN_STORAGE_KEY);
		if (nextObservable) this.loggedInSubject.next(false);
	}

	storeToken(token: AuthorizationToken, sessionOnlyStorage = false): void {
		const expirationDateStr = new Date(Date.now() + (token.expires_in || DEFAULT_EXPIRATION_SECONDS) * 1000).toISOString();

		if (sessionOnlyStorage) {
			sessionStorage.setItem(TOKEN_STORAGE_KEY, token.access_token);
			sessionStorage.setItem(EXPIRATION_DATE_STORAGE_KEY, expirationDateStr);
		} else {
			localStorage.setItem(TOKEN_STORAGE_KEY, token.access_token);
			localStorage.setItem(EXPIRATION_DATE_STORAGE_KEY, expirationDateStr);
		}

		this.loggedInSubject.next(true);
	}

	get currentAuthToken(): AuthorizationToken | null {
		const tokenString = sessionStorage.getItem(TOKEN_STORAGE_KEY) || localStorage.getItem(TOKEN_STORAGE_KEY) || null;

		return tokenString
			? { access_token: tokenString }
			: null;
	}

	get requiredAuthToken(): AuthorizationToken {
		return this.currentAuthToken || throwExpr("An authentication token is required, but the user is not logged in.");
	}

	get isLoggedIn(): boolean {
		if (sessionStorage.getItem(TOKEN_STORAGE_KEY) || localStorage.getItem(TOKEN_STORAGE_KEY)) {
			const expirationString = sessionStorage.getItem(EXPIRATION_DATE_STORAGE_KEY) || localStorage.getItem(EXPIRATION_DATE_STORAGE_KEY);

			if (expirationString) {
				const expirationDate = new Date(expirationString);
				return (expirationDate > new Date());
			} else {
				return true;
			}
		} else {
			return false;
		}
	}

	exchangeCodeForToken(authCode: string): Promise<AuthorizationToken> {
		return this.http.post<AuthorizationToken>(
			this.baseUrl + '/o/code',
			'code=' + encodeURIComponent(authCode),
			{
				observe: "response",
				responseType: "json",
				headers: new HttpHeaders()
					.append('Content-Type', 'application/x-www-form-urlencoded')
			}
		).toPromise()
			.then(r => r.body);
	}

	submitResetPasswordRequest(email: string) {
		return this.http.post<unknown>(
			this.baseUrl + '/v1/user/forgot-password',
			'email=' + encodeURIComponent(email),
			{
				observe: "response",
				responseType: "json",
				headers: new HttpHeaders()
					.append('Content-Type', 'application/x-www-form-urlencoded')
			}
		).toPromise();
	}

	submitForgotPasswordChange(newPassword: string, token: string) {
		return this.http.put<unknown>(
			this.baseUrl + '/v1/user/forgot-password',
			{ password: newPassword, token },
			{
				observe: "response",
				responseType: "json"
			}
			).toPromise();
	}

	handleAuthenticationError() {
		this.logout();

		if (this.navService.currentRouteData.publiclyAccessible !== true) {
			const params = new URLSearchParams(document.location.search.substring(1));
			const redirectUri = params.get("redirect_uri");
			if(redirectUri) localStorage.redirectUri = redirectUri;
			window.location.replace(`/auth/login?authError=${encodeURIComponent("Your session has expired. Please log in to continue.")}`);
		} else {
			window.location.replace(window.location.toString());
		}
	}
}