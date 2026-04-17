export function getToken(): string | null {
  return localStorage.getItem('tickdeck_token');
}

export function setToken(token: string) {
  localStorage.setItem('tickdeck_token', token);
}

export function clearToken() {
  localStorage.removeItem('tickdeck_token');
}

export function isLoggedIn(): boolean {
  return !!getToken();
}
