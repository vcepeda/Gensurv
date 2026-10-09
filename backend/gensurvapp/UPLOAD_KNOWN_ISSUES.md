## Known issue: large uploads stalling on Firefox

**Symptom**: Multi-GB bulk/single submissions (observed on files in the 1–8GB range) intermittently
stall partway through and never complete. The connection stays TCP-`ESTABLISHED` (no RST/FIN), but
`bytes_received` on the server side stops increasing entirely — no timeout, no error, no nginx/gunicorn
log entry, just silence until the client gives up or `client_body_timeout` (1800s) eventually fires.

**Reproduction pattern observed** (2026-07-21/22, real user testing on gensurv.de):
- Same ~7.56GB file stalled twice on Firefox, at the *same* byte offset both times (3,824,069,047 bytes).
- A third Firefox attempt with a different file stalled at a *different* offset (~1.1GB) — so it's not a
  fixed size/duration threshold, which argues against a simple firewall byte/time cap.
- The identical file/network uploaded successfully on Microsoft Edge, same machine, same network,
  no stall.
- Separate successful uploads (5.04GB, 9.04GB) completed fine from a different, slower network
  (~18 Mbps sustained, vs. 45.63 Mbps rated on the network that stalled) — ruling out raw bandwidth
  as the cause.

**Leading hypothesis**: Firefox uses its own certificate store (NSS) instead of the OS store that
Chromium browsers (Chrome/Edge/Brave/Opera) and Safari use. On networks with HTTPS-inspecting
security software (antivirus web-shields, DLP/endpoint proxies — common on institute/corporate
networks), Chromium browsers pick up the injected root CA automatically from the OS store, but
Firefox needs separate configuration. These interception proxies are a well-documented source of
bugs specifically around buffering/re-streaming very large request bodies, and there's a large body
of similar user reports online (Firefox + big uploads + corporate network = stalls) consistent with
what we saw here. Not proven with a packet capture from the affected network — this is the leading
explanation given the evidence, not a confirmed root cause.

**Not the cause** (ruled out during investigation):
- Server-side timeouts: nginx `client_body_timeout`/`proxy_read_timeout`/`proxy_send_timeout` and
  gunicorn `--timeout` are all 1800s and guard against *inactivity gaps*, not total transfer duration —
  confirmed-good uploads ran 35–70 minutes without issue.
- Disk space: verified sufficient free space on `/mnt/storage` (upload media root) and on `/`
  (nginx's `client_body_temp_path`) at the time of the stalls.
- `DATA_UPLOAD_MAX_MEMORY_SIZE` / `FILE_UPLOAD_MAX_MEMORY_SIZE` in `settings.py`: uploads
  are streamed to disk past a 2.5MB threshold, not held in memory.
- Application/validation logic: the precheck (`dry_run=True` on `SingleUploadAPIView`/
  `BulkUploadAPIView`, see `upload_service.py` / `upload_service_num_sar.py`) always completed
  successfully before the real transfer started, and the stalls happened during the raw FASTQ byte
  transfer itself, not during Django's validation/processing.

**Current mitigation**: a warning was added to `HelpGensurvView.vue` and `HelpNumSarView.vue`
recommending Chrome/Edge/Safari over Firefox for large uploads.

**If revisiting this**: the real fix is likely chunked/resumable uploads (e.g. tus.io-style), so a
mid-transfer stall only costs one chunk instead of the whole file — this would sidestep the Firefox/
proxy issue entirely rather than depending on browser choice. Not implemented yet; would need a
new server endpoint to accept/reassemble chunks plus client-side chunking logic in
`UploadGensurvView.vue` / `UploadNumSarView.vue`.
