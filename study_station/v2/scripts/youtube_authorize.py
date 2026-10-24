"""One-time local YouTube consent. Never run this in Actions or commit its output.

pip install google-auth-oauthlib
python scripts/youtube_authorize.py /outside/repo/client_secret.json /outside/repo/youtube-secrets.json
"""
import argparse
import json
import os
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube.readonly']


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('client_file', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--email', default='all.chandansingh@gmail.com', help='Google account to use for consent')
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    if output.is_relative_to(repo):
        ap.error('Save credentials outside the repository.')
    flow = InstalledAppFlow.from_client_secrets_file(str(args.client_file), SCOPES)
    credentials = flow.run_local_server(host='localhost', port=0, access_type='offline', prompt='consent',
                                        login_hint=args.email)
    if not credentials.refresh_token:
        raise SystemExit('No refresh token returned. Repeat consent with the correct Google account.')
    values = {'YOUTUBE_CLIENT_ID': credentials.client_id,
              'YOUTUBE_CLIENT_SECRET': credentials.client_secret,
              'YOUTUBE_REFRESH_TOKEN': credentials.refresh_token}
    # Exclusive creation avoids silently replacing an existing credential file.
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        json.dump(values, fh, indent=2)
        fh.write('\n')
    print('Saved credentials outside the repository. Add the three values as GitHub Actions secrets.')
    print('Never paste the file into chat or commit it. The uploader checks YOUTUBE_CHANNEL_ID before uploading.')


if __name__ == '__main__':
    main()
