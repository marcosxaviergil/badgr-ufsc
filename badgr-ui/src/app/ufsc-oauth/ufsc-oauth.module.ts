import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';

import { UFSCRedirectService } from './services/ufsc-redirect.service';
// ✅ COMENTADO: Remover interceptor que causa redirecionamento automático
// import { UFSCAuthInterceptor } from './services/ufsc-auth-interceptor.service';
// import { UFSCOnlyAuthGuard } from './guards/ufsc-only-auth.guard';
import { UFSCRedirectComponent } from './components/ufsc-redirect.component';

// ✅ COMENTADO: Remover rotas que causam redirecionamento automático
// const routes = [
//   {
//     path: 'accounts/ufsc/login',
//     component: UFSCRedirectComponent
//   }
// ];

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    // ✅ COMENTADO: Remover roteamento que causa redirecionamento
    // RouterModule.forChild(routes)
  ],
  declarations: [
    UFSCRedirectComponent
  ],
  providers: [
    UFSCRedirectService,
    // ✅ COMENTADO: Remover guard e interceptor que causam redirecionamento automático
    // UFSCOnlyAuthGuard,
    // {
    //   provide: HTTP_INTERCEPTORS,
    //   useClass: UFSCAuthInterceptor,
    //   multi: true
    // }
  ],
  exports: [
    UFSCRedirectComponent
  ]
})
export class UFSCOAuthModule {}
