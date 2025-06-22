import { Component, OnInit } from '@angular/core';
import { UFSCRedirectService } from '../services/ufsc-redirect.service';

@Component({
  template: `
    <div class="l-containerxaxis l-containeryaxis l-flex l-flex-justifycenter">
      <div class="shadowcontainer u-animate-dropfade">
        <div class="l-flex l-flex-column l-flex-aligncenter">
          <svg icon="loading" class="icon icon-loading"></svg>
          <h3 class="u-text-h3-bold u-margin-top2x">
            Redirecting to UFSC Authentication...
          </h3>
          <p class="u-text-body u-text-center u-margin-top1x">
            You will be redirected to the UFSC authentication system.
          </p>
        </div>
      </div>
    </div>
  `
})
export class UFSCRedirectComponent implements OnInit {

  constructor(private ufscRedirectService: UFSCRedirectService) {}

  ngOnInit() {
    // Aguardar um pouco para mostrar a mensagem, depois redirecionar
    setTimeout(() => {
      this.ufscRedirectService.redirectToUFSCAuth();
    }, 1500);
  }
}