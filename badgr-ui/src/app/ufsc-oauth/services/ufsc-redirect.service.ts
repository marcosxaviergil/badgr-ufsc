import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { SessionService } from '../../common/services/session.service';

@Injectable()
export class UFSCRedirectService {

  constructor(
    private router: Router,
    private sessionService: SessionService
  ) {}

  /**
   * Redireciona automaticamente para OAuth UFSC
   */
  redirectToUFSCAuth(): void {
    // Buscar provedor UFSC
    const ufscProvider = this.sessionService.enabledExternalAuthProviders
      .find(provider => provider.slug === 'ufsc');
    
    if (ufscProvider) {
      this.sessionService.initiateUnauthenticatedExternalAuth(ufscProvider);
    } else {
      // Fallback: redirecionar diretamente para API
      window.location.href = 'https://api-badges.setic.ufsc.br/accounts/ufsc/login/';
    }
  }

  /**
   * Intercepta tentativas de login/cadastro local
   */
  interceptLocalAuth(): boolean {
    this.redirectToUFSCAuth();
    return false; // Impede navegação local
  }

  /**
   * Configura redirecionamento para frontend URL
   */
  setupFrontendRedirect(): void {
    // Intercepta a URL /accounts/ufsc/login/ no frontend
    if (window.location.pathname === '/accounts/ufsc/login/') {
      this.redirectToUFSCAuth();
    }
  }
}