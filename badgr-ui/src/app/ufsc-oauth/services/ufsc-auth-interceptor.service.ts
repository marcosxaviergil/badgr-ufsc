import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';
import { UFSCRedirectService } from './ufsc-redirect.service';

@Injectable()
export class UFSCAuthInterceptor implements HttpInterceptor {

  constructor(private ufscRedirectService: UFSCRedirectService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Interceptar chamadas para APIs de autenticação local
    const authEndpoints = [
      '/o/token',           // Login local
      '/v1/user/profile',   // Cadastro local
      '/auth/password'      // Mudança de senha
    ];

    const isAuthRequest = authEndpoints.some(endpoint => 
      req.url.includes(endpoint) && req.method === 'POST'
    );

    if (isAuthRequest) {
      // Interceptar e redirecionar para OAuth UFSC
      this.ufscRedirectService.redirectToUFSCAuth();
      
      // Retornar observable vazio para cancelar a requisição
      return new Observable(observer => {
        observer.complete();
      });
    }

    return next.handle(req);
  }
}