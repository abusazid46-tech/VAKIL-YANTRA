export type ApiUser = {
  user_id: string;
  firm_id: string;
  email: string;
  name: string;
  role: string;
  plan: string;
};

export type LoginChallenge = {
  challenge_id: string;
  masked_channel: string;
  expires_in_seconds: number;
  delivery_mode: string;
  preview_otp?: string | null;
};

export type AuthToken = {
  access_token: string;
  token_type: string;
  user: ApiUser;
};

export type InviteUserResponse = {
  invitation_id: string;
  email: string;
  role: string;
  expires_in_seconds: number;
  delivery_mode: string;
  preview_accept_url?: string | null;
};

export type ForgotPasswordResponse = {
  accepted: boolean;
  masked_channel?: string | null;
  delivery_mode?: string | null;
  preview_reset_url?: string | null;
};

export type MatterRecord = {
  id: string;
  firm_id: string;
  title: string;
  court: string;
  matter_type: string;
  client_name: string;
  status: string;
  next_action?: string | null;
  limitation_date?: string | null;
};

export type MatterNote = {
  id: string;
  matter_id: string;
  body: string;
  created_by: string;
  created_at: string;
};

export type MatterTask = {
  id: string;
  matter_id: string;
  title: string;
  due_date?: string | null;
  status: string;
  assigned_to_user_id?: string | null;
  created_by: string;
  created_at: string;
};

export type MatterDetail = MatterRecord & {
  notes: MatterNote[];
  tasks: MatterTask[];
  documents_count: number;
};

export type DocumentRecord = {
  id: string;
  firm_id: string;
  filename: string;
  content_type: string;
  matter_id?: string | null;
  folder_id?: string | null;
  status: string;
  storage_key?: string | null;
  checksum?: string | null;
  created_at?: string | null;
};

export type DocumentDownloadUrl = {
  document_id: string;
  download_url: string;
  expires_in_seconds: number;
};

export type WorkspaceUserOption = {
  user_id: string;
  name: string;
  email: string;
  role: string;
};

export type WorkspaceFolderRecord = {
  id: string;
  name: string;
  parent_folder_id?: string | null;
  owner_user_id: string;
  permission: string;
  notes_count: number;
  documents_count: number;
  created_at: string;
};

export type WorkspaceNoteRecord = {
  id: string;
  folder_id?: string | null;
  title: string;
  body: string;
  owner_user_id: string;
  permission: string;
  updated_at: string;
  created_at: string;
};

export type WorkspaceDocumentRecord = {
  id: string;
  folder_id?: string | null;
  matter_id?: string | null;
  filename: string;
  content_type: string;
  status: string;
  owner_user_id?: string | null;
  permission: string;
  created_at: string;
};

export type WorkspaceShareRecord = {
  id: string;
  resource_type: string;
  resource_id: string;
  resource_name: string;
  grantee_user_id: string;
  grantee_name: string;
  grantee_email: string;
  permission: string;
  created_at: string;
};

export type WorkspaceOverview = {
  folders: WorkspaceFolderRecord[];
  notes: WorkspaceNoteRecord[];
  documents: WorkspaceDocumentRecord[];
  shares: WorkspaceShareRecord[];
  users: WorkspaceUserOption[];
};

export type DashboardResponse = {
  firm: { id: string; name: string; plan: string };
  user: ApiUser;
  stats: {
    matters: number;
    documents: number;
    active_users: number;
    open_tasks: number;
    upcoming_deadlines: number;
  };
  recent_matters: Array<{
    id: string;
    title: string;
    court: string;
    matter_type: string;
    client_name: string;
    next_action?: string | null;
    limitation_date?: string | null;
  }>;
  recent_documents: DocumentRecord[];
  upcoming_deadlines: Array<{
    id: string;
    matter_id: string;
    matter_title: string;
    label: string;
    due_date: string;
    source: string;
    status: string;
  }>;
};

export type FirmUserRecord = {
  membership_id: string;
  user_id: string;
  email: string;
  name: string;
  role: string;
  seat_status: string;
  user_status: string;
  created_at: string;
};

export type InvitationRecord = {
  id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
  created_at: string;
  accepted_at?: string | null;
};

export type Citation = {
  citation_id: string;
  source_title: string;
  section_number?: string | null;
  heading?: string | null;
  quote_excerpt: string;
  similarity_score: number;
  source_url: string;
  chunk_type: string;
};

export type AiResponse = {
  run_id?: string;
  status?: string;
  output_text: string;
  draft_type?: string | null;
  output?: Record<string, any> | null;
  citations: Citation[];
  verification_warning: string;
  retrieved_context_count: number;
};

export type LegalSourceItem = {
  id: string;
  title: string;
  act_number?: string | null;
  enactment_date?: string | null;
  source_type: string;
  jurisdiction: string;
  year: number;
  public_url: string;
  effective_status: string;
};

export type LegalSearchResponse = {
  query: string;
  results: LegalSourceItem[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export async function apiPost<T>(path: string, body: unknown, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(await extractError(response));
  }
  return response.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, body: unknown, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(await extractError(response));
  }
  return response.json() as Promise<T>;
}

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  if (!response.ok) {
    throw new Error(await extractError(response));
  }
  return response.json() as Promise<T>;
}

export async function apiUpload<T>(path: string, formData: FormData, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData
  });
  if (!response.ok) {
    throw new Error(await extractError(response));
  }
  return response.json() as Promise<T>;
}

async function extractError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return typeof data.detail === "string" ? data.detail : "Request failed";
  } catch {
    return "Request failed";
  }
}
