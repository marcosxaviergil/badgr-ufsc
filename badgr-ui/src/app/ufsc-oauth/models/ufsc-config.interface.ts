export interface UFSCOAuthConfig {
  authUrl: string;
  clientId: string;
  redirectUri: string;
  scope: string[];
}

export interface UFSCUserData {
  id: string;
  login: string;
  nomeSocial: string;
  email: string;
  emailInstitucional: string;
  nome: string;
}
