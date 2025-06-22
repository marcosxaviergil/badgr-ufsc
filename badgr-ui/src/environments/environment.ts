// The file contents for the current environment will overwrite these during build.
// The build system defaults to the dev environment which uses `environment.ts`, but if you do
// `ng build --env=prod` then `environment.prod.ts` will be used instead.
// The list of which env maps to which file can be found in `.angular-cli.json` or `angular.json`.

import { BadgrEnvironment } from './badgr-environment';

export const environment: BadgrEnvironment = {
  production: false,
  config: {
    api: {
      baseUrl: 'https://api-badges.setic.ufsc.br'
    },
    help: {
      email: 'badges@sistemas.ufsc.br'
    },
    features: {
      disableRegistration: true,
      // ✅ VOLTA: Configuração estática que funciona
      externalAuthProviders: [
        {
          slug: 'ufsc',
          label: 'UFSC',
          imgSrc: '/static/images/ufsc-logo.svg',
          color: '#005580'
        }
      ]
    },
    googleAnalytics: {
      trackingId: ''
    },
    assertionVerifyUrl: '',
    theme: {} as any
  }
};
