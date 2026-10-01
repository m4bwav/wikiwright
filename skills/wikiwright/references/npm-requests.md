# npm packages that make requests

Read this for an npm package that fetches, calls back or opens sockets (`scaffold --requests` or `--by-host`), and for a golden capture that records through its own proxy. The rest is in [npm.md](npm.md).

## Rules for requests

A package that fetches, calls back or opens sockets is verified against the local fixture server only, as its own tests do. The internet never produces an output shown on a page: sites change their titles, go down and rate-limit, and the next run of the script would disagree with the page. Where a page wants a familiar URL (`https://example.com/`), show the real call and state that the output shown came from a local fixture serving the same HTML; or keep the page's example on the fixture address.

- A refused connection: listen on a free port, close it, and use that address.
- A proxy recipe: Node's environment proxy support (`NODE_USE_ENV_PROXY=1` or `--use-env-proxy`) tunnels even `http:` URLs with `CONNECT` (Node 24.18.0, 2026-09-28). A stand-in proxy answers `connect` with `HTTP/1.1 200 Connection Established` and hands the socket to the fixture server (`server.emit('connection', socket)`); target an `.invalid` host so the direct request can never leave the machine (L-112 `fetch-proxy-connect`). The stand-in refuses every target but the fixture, so a recipe bug cannot send a request out through it. undici 8's `ProxyAgent` sends an absolute-form `GET http://...` for an `http:` target where undici 7 sends `CONNECT`: handle both (L-131).

## Packages that request by host name through their dependencies

When the package's requests go through its dependencies to the hosts its input names, and its output is computed from the host (a site name, a domain, a check of the top-level domain), the fixture address cannot stand in for the real one: the page would show `127.0.0.1` where the reader gets `example.com`. Two routes worked (markdown-plain-link-replacer 2.0.0, 2026-09-29):

- **A `fetch` wrapper** that sends every request to the fixture with the meant URL in a header (`x-fixture-url`), loaded in-process or with `node --import` (L-115 `route-fetch-preload`). Light, Node only, and only for a package that calls the global `fetch` at call time. The repository's own test helpers often have one; read them first.
- **A proxy by host name with TLS** (L-116 `by-host-name-proxy`; [../templates/npm/host-fixture.mjs](../templates/npm/host-fixture.mjs), which the template imports: read its header, not its body). Pages are served from a plain server and a TLS server keyed by host and path, behind a stand-in proxy on 127.0.0.1 that answers `CONNECT` and hands the socket to the TLS server for port 443 and to the plain server for any other port. This route also covers Deno, Bun, the package managers and old versions in child processes, and it uses the transport the package really uses. What each runtime needed, measured on 2026-09-29:
  - Node 24.18.0: `NODE_USE_ENV_PROXY=1` with `HTTP_PROXY` and `HTTPS_PROXY`, all read at startup (set them in the child's environment; setting `process.env` later does nothing). Node tunnels `http:` links with `CONNECT host:80` too (L-112).
  - Node 20.20.2: no `NODE_USE_ENV_PROXY`; preload undici's `EnvHttpProxyAgent` (`npm install undici@7`, a two-line `--require` file calling `setGlobalDispatcher(new EnvHttpProxyAgent())`). The script's own process can use undici's `ProxyAgent` with `requestTls: {ca}`.
  - Trust: a throwaway CA and a server certificate it signed (openssl), the CA given as `NODE_EXTRA_CA_CERTS` (Node, Bun; read at startup) and `DENO_CERT` (Deno). Deno 2.9.6 refused one self-signed certificate marked as a CA as the server's own. Without trust, https links fail silently while http links work.
  - Deno 2.9.6 and Bun 1.4.2 read `HTTP_PROXY` and `HTTPS_PROXY` themselves. Deno resolves `npm:` from the `node_modules` of the nearest folder with a `package.json`, so run it where the package is installed, or in a folder with no `package.json` above it (L-021).
  - `NODE_OPTIONS` reads a backslash as an escape: give preload paths with forward slashes.
  - Decide a Node's route with a probe to an `.invalid` host (never a real one), and print one case with the requests the fixture saw, so a silent routing failure cannot pass for the package's behaviour.
- **Guard** every child with a preload that refuses any socket not to 127.0.0.1, reading the options from `Array.isArray(args[0]) ? args[0][0] : args[0]`: `net.connect()` passes its arguments as one array, so a guard reading `args[0].host` stops https but lets plain http reach the internet (L-117 `guard-normalised-args`; it did in the first Node 20 run).

## Golden captures that record through a proxy with TLS

A capture that routes an old version's requests through its own recording proxy (request 2.88 honours `HTTP_PROXY` and `HTTPS_PROXY`) replays against the old version unchanged. Against a new major that uses `fetch`, the copies needed four changes, none to the cases (markdown-plain-link-replacer 1.1.16 against 2.0.0, 2026-09-29; L-113 `replay-requesting-capture`):

1. the bin's path read from package.json (`cli.js` became `dist/cli.mjs`);
2. a dependency lookup that answers `none` for packages the new major dropped;
3. undici's `EnvHttpProxyAgent` installed right after the capture sets the proxy variables, in the capture and, through `NODE_OPTIONS=--require <file>`, in its CLI children: `NODE_USE_ENV_PROXY=1` alone fails, because the capture sets the variables only once its server listens;
4. a fixture-server copy whose `connect` handler serves ports other than 443 in plain HTTP, because `fetch` tunnels `http:` links too.

`NODE_TLS_REJECT_UNAUTHORIZED=0`, set by the capture at run time, is read per connection and covered the certificate. Compare the answer, the callback timing and the request lists apart, the request lists without the `CONNECT` lines and without how each request arrived; mask link titles when a dependency's new major reads titles differently, and count title-only differences separately. package-modernize's capture template now removes all four: it reads the bin and the dependencies (its C-20260929-1), and `capture-proxy.cjs` sets the proxy variables before the package loads and routes CONNECT by port (its C-20260929-3, L-125). stack-exchange-markdown-retriever's 1.1.7 capture (2026-09-29), which predates both, needed changes 1 to 3; 2.0.0 only tunnels to port 443.

Related: builds on [npm.md](npm.md); see also [golden-captures.md](golden-captures.md), [nuget-requests.md](nuget-requests.md), [page-sets-cli.md](page-sets-cli.md).
