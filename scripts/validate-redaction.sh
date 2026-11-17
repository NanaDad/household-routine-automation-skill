#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
if grep -RInE --exclude-dir=.git --exclude=validate-redaction.sh '(sk-[A-Za-z0-9_-]{16,}|xox[baprs]-[A-Za-z0-9-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\+?[0-9][0-9 ()-]{7,}[0-9])' "$ROOT"; then
  echo 'Potential secret or personal contact data found; review before publishing.' >&2
  exit 1
fi
# Household identity / bot labels must stay out of the portable skill.
if grep -RInE --exclude-dir=.git --exclude=validate-redaction.sh '(나윤|나린|나윤맘|nayunmom|nayun|민구|다은|임다은|평택|장당|숲속향기|꿈꾸는숲|kidsnote|MG_Drive|workspace-nayun)' "$ROOT"; then
  echo 'Potential household identity or bot-label data found; review before publishing.' >&2
  exit 1
fi
for name in .env auth-profiles.json credentials token secret; do
  if find "$ROOT" -name "$name" -print | grep -q .; then
    echo "Sensitive/runtime artifact found: $name" >&2
    exit 1
  fi
done
for ext in jpg jpeg png heic sqlite db log; do
  if find "$ROOT" -type f -name "*.$ext" -print | grep -q .; then
    echo "Sensitive/runtime artifact extension found: .$ext" >&2
    exit 1
  fi
done
echo 'Redaction scan passed (manual review still required).'
