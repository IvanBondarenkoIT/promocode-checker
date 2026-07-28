/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DEFAULT_POINT_ID?: string;
  readonly VITE_HEARTBEAT_SECONDS?: string;
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
