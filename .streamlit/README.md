# `.streamlit/`: Streamlit settings

Streamlit reads `.streamlit/config.toml` from the folder it is started in,
which is one more reason to start the app from the repo root. The file sets
the web server (port, upload size) and the look of the app. No Python code
reads it; the app code only depends on two of its values, which are copied
in `dahu_2_config.py`.

## Files

- **`config.toml`**: the settings, in TOML format (a simple `key = value`
  text format; `[server]` starts a section, `[[theme.fontFaces]]` adds one
  item to a list). Open it to change the port, the upload limit, colours or
  fonts.
  - `[client] showSidebarNavigation = false`: hides Streamlit's automatic
    list of pages. The sidebar is drawn by `browser_side_bar` in
    `pages/components/browsing.py` instead.
  - `[server] port = 80`: the app answers at `http://localhost` (port 80
    is the default for web addresses).
  - `[server] maxUploadSize`: largest file users can upload, in MB.
  - `[server] enableStaticServing = false`: Streamlit does not publish
    the repo's `static/` folder at the URL `app/static/`.
  - `[[theme.fontFaces]]`: the Inter and JetBrains Mono fonts, pointing
    at the files of the repo's `static/` folder through `app/static/...`
    URLs. Streamlit's documentation says such fonts need
    `enableStaticServing = true`, so they may not load.
  - `[theme]` and `[theme.sidebar]`: colours, fonts and corner rounding.

**Two settings are duplicated in `dahu_2_config.py`. Change both places
together**, or links and limits will disagree:

- the port, in `port` here and inside `DOMAIN` (both the production and
  development blocks) in `dahu_2_config.py`;
- the upload limit, in `maxUploadSize` here and `MAX_UPLOAD_SIZE_MB` in
  `dahu_2_config.py`.

## Common tasks

### Change the port

1. Edit `port` in `config.toml`.
2. Edit the port at the end of both `DOMAIN` values in `dahu_2_config.py`.
3. Restart Streamlit.

### Change the maximum upload size

1. Edit `maxUploadSize` in `config.toml` (in MB).
2. Edit `MAX_UPLOAD_SIZE_MB` in `dahu_2_config.py` to the same value.
3. Restart Streamlit.

### Change a colour or font

1. Edit the `[theme]` section of `config.toml`. Font files go in
   `static/`, with one `[[theme.fontFaces]]` entry per file.
2. Restart Streamlit.
