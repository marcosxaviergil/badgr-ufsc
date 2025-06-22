import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';

import { UFSCRedirectService } from './services/ufsc-redirect.service';
import { UFSCAuthInterceptor } from './services/ufsc-auth-interceptor.service';
import { UFSCOnlyAuthGuard } from './guards/ufsc-only-auth.guard';
import { UFSCRedirectComponent } from './components/ufsc-redirect.component';

const routes = [
  {
    path: 'accounts/ufsc/login',
    component: UFSCRedirectComponent
  }
];

@NgModule({
  imports: [
    CommonModule,
    HttpClientModule,
    RouterModule.forChild(routes)
  ],
  declarations: [
    UFSCRedirectComponent
  ],
  providers: [
    UFSCRedirectService,
    UFSCOnlyAuthGuard,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: UFSCAuthInterceptor,
      multi: true
    }
  ],
  exports: [
    UFSCRedirectComponent
  ]
})
export class UFSCOAuthModule {}