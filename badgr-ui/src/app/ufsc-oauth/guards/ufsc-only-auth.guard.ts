import { Injectable } from '@angular/core';
import { CanActivate, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { UFSCRedirectService } from '../services/ufsc-redirect.service';
import { SessionService } from '../../common/services/session.service';

@Injectable()
export class UFSCOnlyAuthGuard implements CanActivate {

  constructor(
    private router: Router,
    private ufscRedirectService: UFSCRedirectService,
    private sessionService: SessionService
  ) {}

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    // Rotas que devem ser interceptadas e redirecionadas para OAuth UFSC
    const authRoutes = [
      '/auth/login',
      '/auth/signup', 
      '/signup',
      '/login'
    ];

    if (authRoutes.includes(state.url)) {
      // Se usuário já está logado, permitir acesso
      if (this.sessionService.isLoggedIn) {
        return true;
      }

      // Se não está logado, redirecionar para OAuth UFSC
      this.ufscRedirectService.redirectToUFSCAuth();
      return false;
    }

    return true;
  }
}