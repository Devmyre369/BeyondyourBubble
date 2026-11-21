p = 'accounts/urls.py'
s = open(p).read()
marker = '    path(\\\\n        "me/settings/",'
idx = s.find(marker)
if idx != -1:
    s = s[:idx] + ']\n'
s = s.rstrip()
if not s.endswith(']'):
    s += '\n]'
# now append proper paths before final ]
s = s[:-2]  # remove ']\n'? careful
# Rebuild: take up to last ']' and insert before it
idx2 = s.rfind(']')
prefix = s[:idx2]
suffix = s[idx2:]
addition = '''    path(
        "me/settings/",
        UserSettingsView.as_view(),
        name="my-settings",
    ),
    path(
        "me/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "me/delete-account/",
        DeleteAccountView.as_view(),
        name="delete-account",
    ),
'''
s = prefix + addition + suffix
open(p, 'w').write(s)
print('done')
