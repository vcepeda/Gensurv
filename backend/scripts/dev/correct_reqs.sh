# 1) Start from your current file
cp requirements.txt requirements.pip.txt

# 2) Drop OS-managed / non-pip lines
sed -i -E '/^(python-apt|ubuntu-pro-client|ufw|unattended-upgrades|language-selector|command-not-found|distro-info|dbus-python|PyGObject|systemd-python|iotop|sos|wadllib|python-debian|certbot|certbot-nginx|acme|josepy)\b/d' requirements.pip.txt

# 3) Remove backports not needed on 3.12
sed -i -E '/^(importlib-metadata|zipp|backports\.zoneinfo)\b/d' requirements.pip.txt

# 4) Bump critical pins for 3.12 compatibility
sed -i -E 's/^numpy==.*/numpy>=1.26.4/' requirements.pip.txt
sed -i -E 's/^pandas==.*/pandas>=2.2.2/' requirements.pip.txt
sed -i -E 's/^Jinja2==.*/Jinja2>=3.1.4/' requirements.pip.txt
sed -i -E 's/^MarkupSafe==.*/MarkupSafe>=2.1.5/' requirements.pip.txt
sed -i -E 's/^[Cc]lick==.*/click>=8.1.7/' requirements.pip.txt
sed -i -E 's/^requests==.*/requests>=2.31.0/' requirements.pip.txt
# keep urllib3 <3 for broad compat
grep -q '^urllib3' requirements.pip.txt && \
  sed -i -E 's/^urllib3==.*/urllib3>=1.26.18,<3/' requirements.pip.txt || \
  printf 'urllib3>=1.26.18,<3\n' >> requirements.pip.txt
sed -i -E 's/^idna==.*/idna>=3.7/' requirements.pip.txt

# 5) Either bump or drop Twisted/zope stack (often not needed)
#commented out Twisted bump for now; may be needed for certbot
#sed -i -E 's/^Twisted==.*/Twisted>=24.7.0/' requirements.pip.txt || true

# Update pins in-place
sed -i -E 's/^Twisted==.*/Twisted>=24.7.0/' requirements.pip.txt
sed -i -E 's/^attrs==.*/attrs>=22.2.0/' requirements.pip.txt
# If present, bump or drop PyICU
grep -q '^PyICU==' requirements.txt && sed -i -E 's/^PyICU==.*/PyICU>=2.13/' requirements.pip.txt || true



sed -i -E 's/^zope\.interface==.*/zope.interface>=6.3/' requirements.pip.txt || true

# 6) Ensure gunicorn is listed for your venv
grep -qi '^gunicorn' requirements.pip.txt || echo 'gunicorn>=22,<23' >> requirements.pip.txt

# bump these to Py3.12-friendly versions
sed -i -E 's/^zope\.hookable==.*/zope.hookable>=7.0/' requirements.pip.txt
sed -i -E 's/^zope\.component==.*/zope.component>=6.0/' requirements.pip.txt
sed -i -E 's/^zope\.event==.*/zope.event>=5.0/' requirements.pip.txt

sed -i -E 's/^Automat==.*/Automat>=24.8.1/' requirements.pip.txt
sed -i -E 's/^incremental==.*/incremental==24.7.2/' requirements.pip.txt


# try again (I recommend installing all on the first pass)
./preflight_py_env.sh -r requirements.pip.txt -v ~/venvs/Gensurv_venv --install-all
#done


