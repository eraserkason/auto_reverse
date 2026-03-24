export interface AuthenticatedUser {
  id: number;
  username: string;
  displayName: string;
  role: string;
  createdAt: string;
}

export interface MockUser {
  id: string;
  username: string;
  password: string;
  displayName: string;
  role: string;
}

export interface AuthSession {
  token: string;
  user: AuthenticatedUser;
  loginAt: string;
  expiresAt: string;
}
