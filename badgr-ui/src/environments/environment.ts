// The file contents for the current environment will overwrite these during build.
// The build system defaults to the dev environment which uses `environment.ts`, but if you do
// `ng build --env=prod` then `environment.prod.ts` will be used instead.
// The list of which env maps to which file can be found in `.angular-cli.json` or `angular.json`.

import { BadgrEnvironment } from './badgr-environment';

export const environment: BadgrEnvironment = {
  production: true,  // ✅ Corrigido para produção
  config: {
    api: {
      baseUrl: 'https://api-badges.setic.ufsc.br'  // ✅ URL da API em produção
    },
    help: {
      email: 'badges@sistemas.ufsc.br'
    },
    features: {},
    googleAnalytics: {
      trackingId: ''
    },
    assertionVerifyUrl: '',
    theme: {} as any
  }
};
