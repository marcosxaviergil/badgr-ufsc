import { enableProdMode } from "@angular/core";
import { platformBrowserDynamic } from "@angular/platform-browser-dynamic";
import { AppModule } from "./app/app.module";
import { environment } from "./environments/environment";

// HACK: Workaround how array-uniq v1 checks for features... seems hardcoded for node usage
(window as any)["global"] = window;

// Store the initial window location for query param fallback
(window as any)["initialLocationHref"] = window.location.href.toString();

// ✅ Ativa modo produção se for o caso
if (environment.production) {
  enableProdMode();
}

platformBrowserDynamic()
  .bootstrapModule(AppModule)
  .catch(err => console.error(err));
