# Live Railway Data Integration Guide

This guide details the specifications, authentication protocols, and resilience mechanisms for integrating the Railway Block Planner with Indian Railways enterprise systems and authoritative data sources.

---

## 1. Authorized External Data Sources

### 1.1 CRIS / ISRO RTIS (Real-time Train Information System)
- **Authority**: Centre for Railway Information Systems (CRIS) in partnership with the Indian Space Research Organisation (ISRO).
- **Technology**: Locomotive-mounted MSS (Mobile Satellite Service) and 4G/GPRS transponders transmitting high-frequency GPS position fixes, speed, and heading every 30 seconds.
- **Protocol**: HTTPS REST / JSON or WebSockets (WSS).
- **Authentication**:
  - OAuth 2.0 Client Credentials (`client_id`, `client_secret`).
  - Mutual TLS (mTLS) with X.509 client certificate and RSA private key signed by the CRIS Root Certificate Authority.
- **Environment Variables**:
  ```bash
  RTIS_API_BASE_URL=https://rtis.cris.org.in/api/v1
  RTIS_CLIENT_ID=your_cris_client_id
  RTIS_CLIENT_SECRET=your_cris_client_secret
  RTIS_AUTH_TOKEN=your_oauth_token
  RTIS_MTLS_CERT_PATH=/etc/ssl/certs/cris_rtis_client.crt
  RTIS_MTLS_KEY_PATH=/etc/ssl/private/cris_rtis_client.key
  RTIS_POLL_INTERVAL_SEC=15.0
  ```
- **Fallback / Unconfigured Behavior**:
  When credentials are omitted or invalid, the provider enters state `AUTHENTICATION_REQUIRED` or `DISCONNECTED`. The platform displays an `AUTHENTICATION REQUIRED` pill and **never fabricates mock trains as live feeds**.

---

### 1.2 Indian Railways NTES (National Train Enquiry System) / API Setu
- **Authority**: Ministry of Railways via National Informatics Centre (NIC) / API Setu.
- **Payload**: Station arrival/departure timings, day-to-day timetable modifications, cancellation notices, platform assignments, and current delay minutes across master train schedules.
- **Protocol**: HTTPS REST JSON.
- **Authentication**: API Key via `X-API-KEY` or `Authorization: Bearer <key>`.
- **Environment Variables**:
  ```bash
  NTES_API_BASE_URL=https://apisetu.gov.in/api/railway/ntes/v1
  NTES_API_KEY=your_apisetu_key_here
  NTES_POLL_INTERVAL_SEC=30.0
  ```
- **Resilience**: Caches last known station passage events. Circuit breaker opens after 5 consecutive HTTP 5xx errors or timeouts (>10s).

---

### 1.3 Open Government Data Platform (data.gov.in)
- **Authority**: Government of India Open Data initiative.
- **Payload**: Pan-India master timetable reference, route kilometer milestones, and official station directory.
- **Protocol**: HTTPS REST with API Key.
- **Environment Variables**:
  ```bash
  OGD_API_KEY=your_data_gov_in_api_key
  OGD_RESOURCE_ID=your_resource_id
  OGD_POLL_INTERVAL_SEC=3600.0
  ```
- **Caching**: Stored locally in `data/ogd_timetables_cache.json` with a 24-hour time-to-live (TTL). If the portal is offline, local cache is utilized transparently.

---

## 2. Circuit Breakers & Fault Tolerance

Every external data provider subclasses `BaseRailwayDataProvider` (`backend/providers/base.py`) which implements an enterprise circuit breaker pattern:

| Metric | Default Value | Description |
| :--- | :--- | :--- |
| **Failure Threshold** | 3 - 5 consecutive errors | Number of HTTP failures or timeouts before tripping the circuit. |
| **Trip Action** | State $\to$ `UNAVAILABLE` | Stops issuing external outbound requests to prevent hammering remote endpoints. |
| **Timeout Window** | 45.0 - 60.0 seconds | Duration to wait before transitioning into `DEGRADED` (half-open) state. |
| **Half-Open Probe** | 1 test request | If successful, transitions to `CONNECTED` and resets error counter; if failed, resets timeout window. |

---

## 3. Development Simulation Provider

For offline testing, continuous integration (CI), and operator training environments where live CRIS/ISRO connections are not accessible:

- **Enabling Simulation**:
  ```bash
  ENABLE_SIMULATION_PROVIDER=true
  SIMULATION_TICK_INTERVAL_SEC=5.0
  ```
- **Disabling Simulation**:
  ```bash
  ENABLE_SIMULATION_PROVIDER=false
  ```

### Strict Compliance & Authenticity Rules
1. **Prominent Stamping**: Every simulated train state, event, and telemetry packet carries:
   - `data_quality: "SIMULATED"`
   - `provenance.disclaimer: "DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)"`
2. **Dashboard UI Disclaimer**: When simulation is active, the dashboard header prominently displays a persistent warning banner:
   `[ DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA) ]`
3. **No Masquerading**: Synthetic feeds are never disguised as live CRIS/NTES feeds.
