import { api } from '../client'

export interface GmailAccount {
  email: string
  authenticated: boolean
  scopes: string[]
  added_date: string
}

export interface GmailAccountsResponse {
  accounts: Record<string, GmailAccount>
}

export function listGmailAccounts(): Promise<GmailAccountsResponse> {
  return api('gmail_accounts_list')
}

export function removeGmailAccount(accountName: string): Promise<{ success: boolean }> {
  return api('gmail_account_remove', { body: { account_name: accountName } })
}

export function startGmailOAuth(accountName: string): Promise<{ auth_url: string }> {
  return api('gmail_oauth_start', { body: { account_name: accountName } })
}
