export type CashierResult =
  | "valid"
  | "redeemed"
  | "not_found"
  | "expired"
  | "used"
  | "invalid_format"
  | "out_of_scope";

export type CashierCodeResponse = {
  result: CashierResult;
  code: string;
  point_id: string;
  status: string | null;
  expires_at: string | null;
  redeemed_at: string | null;
  log_id: number | null;
  campaign_code?: string | null;
  campaign_name?: string | null;
  campaign_ends_at?: string | null;
  campaign_kind?: string | null;
  active_campaign_kind?: string | null;
};

export type HeartbeatResponse = {
  ok: boolean;
  point_id: string;
  server_time: string;
};
