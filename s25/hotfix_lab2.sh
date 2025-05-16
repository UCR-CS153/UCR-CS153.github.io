cd /workspaces/lab2-*
hash=$(md5sum .github/workflows/classroom.yml | awk '{ print $1 }')
workflows="bmFtZTogTGFiMiBBdXRvZ3JhZGVyCgpvbjoKICBwdXNoOgogICAgYnJhbmNoZXM6CiAgICAgIC0g
bWFzdGVyCgpqb2JzOgogIHJ1bi1zY3JpcHQ6CiAgICBydW5zLW9uOiBzZWxmLWhvc3RlZAogICAg
dGltZW91dC1taW51dGVzOiAxMAoKICAgIHN0ZXBzOgogICAgLSBuYW1lOiBDaGVja291dCBjb2Rl
CiAgICAgIHVzZXM6IGFjdGlvbnMvY2hlY2tvdXRAdjQKCiAgICAtIG5hbWU6IERvd25sb2FkIGFu
ZCBydW4gc2NyaXB0CiAgICAgIHJ1bjogfCAKICAgICAgICB3Z2V0IC1xIGh0dHBzOi8vdWNyLWNz
MTUzLmdpdGh1Yi5pby9zMjUvbGFiMl9hdXRvZ3JhZGVyLnB5ID4gL2Rldi9udWxsICAyPiYxCiAg
ICAgICAgcHl0aG9uMyBsYWIyX2F1dG9ncmFkZXIucHkKCiAgICAtIG5hbWU6IENsZWFuIHVwCiAg
ICAgIHJ1bjogfAogICAgICAgIHJtIC1mIGxhYjJfYXV0b2dyYWRlci5weQogICAgICAgIHJtIC1m
IHRlc3RfLio="
if [ "$hash" == "e45a070c9326679e7708631c3a53001e" ]; then
    echo "The file is okay, you are good to go!"
    exit 0
else
    echo "Fixing the file..."
    echo "$workflows" | base64 -d > .github/workflows/classroom.yml
    echo "The file has been fixed."
fi
