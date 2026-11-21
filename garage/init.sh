#!/bin/sh
# One-shot Garage bootstrap through the admin API: layout, access key, bucket.
# Idempotent; runs as the `garage-init` compose service.
set -eu

ADMIN="${GARAGE_ADMIN_URL:-http://garage:3903}"
TOKEN="${GARAGE_ADMIN_TOKEN:-investwatch-dev-admin-token}"
ACCESS_KEY="${S3_ACCESS_KEY:-GK0123456789abcdef01234567}"
SECRET_KEY="${S3_SECRET_KEY:-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef}"
BUCKET="${S3_BUCKET:-investwatch-evidence}"

api() {
  curl -sf -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" "$@"
}

until api "$ADMIN/v2/GetClusterStatus" >/tmp/status.json 2>/dev/null; do
  sleep 1
done

NODE_ID=$(grep -o '"id" *: *"[0-9a-f]\{64\}"' /tmp/status.json | head -n 1 | grep -o '[0-9a-f]\{64\}')

if ! api "$ADMIN/v2/GetClusterLayout" | grep -q "$NODE_ID"; then
  api -X POST "$ADMIN/v2/UpdateClusterLayout" \
    -d "{\"roles\":[{\"id\":\"$NODE_ID\",\"zone\":\"dc1\",\"capacity\":1073741824,\"tags\":[]}]}" >/dev/null
  api -X POST "$ADMIN/v2/ApplyClusterLayout" -d '{"version":1}' >/dev/null
fi

api -X POST "$ADMIN/v2/ImportKey" \
  -d "{\"accessKeyId\":\"$ACCESS_KEY\",\"secretAccessKey\":\"$SECRET_KEY\",\"name\":\"local-dev\"}" >/dev/null 2>&1 || true

api -X POST "$ADMIN/v2/CreateBucket" -d "{\"globalAlias\":\"$BUCKET\"}" >/dev/null 2>&1 || true

BUCKET_ID=$(api "$ADMIN/v2/GetBucketInfo?globalAlias=$BUCKET" | grep -o '"id" *: *"[0-9a-f]\{64\}"' | head -n 1 | grep -o '[0-9a-f]\{64\}')
api -X POST "$ADMIN/v2/AllowBucketKey" \
  -d "{\"bucketId\":\"$BUCKET_ID\",\"accessKeyId\":\"$ACCESS_KEY\",\"permissions\":{\"read\":true,\"write\":true,\"owner\":true}}" >/dev/null
echo "garage ready: bucket=$BUCKET"
