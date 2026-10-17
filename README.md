# Task 9: CI/CD Pipeline for a Flask App with GitHub Actions

A small Flask Task Manager with automated tests, a Docker build check, and an **optional** automatic deployment to an Ubuntu AWS EC2 instance (Gunicorn + systemd + Nginx).

Written for a beginner on **Windows 11 with WSL Ubuntu**.

---

## 1. Project directory structure

```
python-cicd-app/
├── app.py                       # Flask application
├── requirements.txt             # Python dependencies
├── tests/
│   └── test_app.py              # pytest tests
├── Dockerfile                   # Container image definition
├── .dockerignore                # Files kept out of the Docker image
├── .gitignore                   # Files kept out of Git
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # GitHub Actions pipeline
├── deploy/
│   ├── setup-server.sh          # ONE-TIME EC2 setup (Nginx, systemd)
│   └── remote-deploy.sh         # Runs on EC2 at each deploy
└── README.md
```

## 2. What each file does

| File | Purpose |
|---|---|
| `app.py` | The web app. Home page (`/`) to add/complete/delete tasks, and `/health` returning `{"status": "ok"}`. Tasks live in memory, no database. |
| `requirements.txt` | Flask (web framework), Gunicorn (production server), pytest (tests). |
| `tests/test_app.py` | Checks the home page, `/health`, and add/toggle/delete behaviour. |
| `Dockerfile` | Packages the app into a container that runs under Gunicorn as a non-root user. |
| `.dockerignore` | Keeps tests, git data and secrets out of the image. |
| `.gitignore` | Stops virtual environments, caches and secrets (`.env`, `*.pem`) from being committed. |
| `.github/workflows/ci-cd.yml` | The pipeline: test, Docker build, optional deploy. |
| `deploy/setup-server.sh` | Prepares a fresh EC2 server once. |
| `deploy/remote-deploy.sh` | Installs dependencies and restarts the app on each deploy. |

## 3. What are CI and CD?

- **CI (Continuous Integration):** every time you push code, an automatic job builds and tests it. You find broken code in minutes, not weeks.
- **CD (Continuous Deployment):** if CI passes, the new version is automatically released to a server. No manual copying.

**GitHub Actions** is GitHub's built-in automation. You describe a **workflow** in a YAML file under `.github/workflows/`. A workflow has **jobs**; each job runs on a fresh virtual machine (**runner**) and is made of **steps** (commands or reusable **actions** like `actions/checkout`). **Events** (a push, a pull request) trigger workflows.

In this project:

```
push / pull request to main
        │
   [ test ]  ── pytest on Python 3.11 and 3.12
        │
 [ docker-build ] ── build image + /health smoke test
        │
   [ deploy ]  ── ONLY on push to main, ONLY if DEPLOY_ENABLED=true
```

`deploy` uses `needs: [test, docker-build]`, so **if tests fail, nothing is deployed**. It never runs on pull requests.

---

## 4. Run the app locally (WSL Ubuntu)

Open the Ubuntu (WSL) terminal.

```bash
# Install Python tools (one time)
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git

cd python-cicd-app

python3 -m venv venv              # create an isolated Python environment
source venv/bin/activate          # activate it
pip install -r requirements.txt   # install dependencies

python -m pytest -v               # run the tests
python app.py                     # start the app on http://127.0.0.1:5000
```

Open http://127.0.0.1:5000 in your Windows browser (WSL forwards localhost). Check http://127.0.0.1:5000/health.

Optional Docker test (needs Docker installed in WSL or Docker Desktop):

```bash
docker build -t python-task-manager .
docker run --rm -p 8000:8000 python-task-manager
# visit http://localhost:8000
```

---

## 5. Create the GitHub repository and push

1. On github.com click **New repository**. Name it `python-cicd-app`. Leave "Add README/.gitignore" **unchecked** (you already have them). Create it.
2. Tell Git who you are (one time):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```
3. Push the project:
   ```bash
   cd python-cicd-app
   git init -b main                 # start a repo with branch "main"
   git add .                        # stage all files (.gitignore excludes junk)
   git status                       # review: no venv/, no .pem files!
   git commit -m "Initial commit: Flask app with CI/CD pipeline"
   git remote add origin https://github.com/YOUR-USERNAME/python-cicd-app.git
   git push -u origin main
   ```
   When asked for a password, use a **Personal Access Token** (GitHub > Settings > Developer settings > Personal access tokens), not your account password. Or use `gh auth login` if you have the GitHub CLI.

---

## 6. Test the CI pipeline

1. Open your repo on GitHub and click the **Actions** tab.
2. You should see a run named **CI/CD** for your push. A yellow dot means running, green check means passed, red cross means failed.
3. Click the run. You will see the jobs **Run tests** (twice, once per Python version) and **Build Docker image**. The **Deploy to EC2** job shows as skipped, which is expected until you enable deployment.
4. Click a job, then a step, to expand its log.

**Prove that CI blocks bad code:**

```bash
git checkout -b break-test
# In tests/test_app.py change:  assert response.status_code == 200
# in test_health_endpoint to:   assert response.status_code == 500
git commit -am "Break a test on purpose"
git push -u origin break-test
```

Open a pull request into `main` on GitHub. The checks fail with a red cross. Fix the test, push again, and they turn green. Merging to `main` only after green checks is the habit CI is built for.

**Optional:** in repo **Settings > Branches > Add rule** for `main`, enable "Require status checks to pass before merging".

### Reading logs and fixing failed jobs

Click the failed job, find the step with the red cross, and read the last lines of its log. The real error is usually right above "Process completed with exit code 1".

---

## 7. OPTIONAL: Automatic deployment to AWS EC2

Everything in this section is optional. Without it, the pipeline still does CI.

### 7.1 Launch the EC2 instance

1. AWS Console > **EC2 > Launch instance**.
2. Name: `python-app-server`. AMI: **Ubuntu Server 24.04 LTS**. Type: `t3.micro` (or `t2.micro`, free-tier eligible).
3. **Key pair:** create a new one (type `ed25519`, format `.pem`) and download it. Keep it private.
4. **Network settings / Security group:** allow
   - **SSH (22)**, Source: **My IP** (not 0.0.0.0/0)
   - **HTTP (80)**, Source: **Anywhere (0.0.0.0/0)**
5. Launch, then copy the **Public IPv4 address**.

> GitHub-hosted runners use changing IP addresses, so SSH must accept connections from them. Security still comes from key-only login and the pinned host key below. For a throw-away practice server this is acceptable; for real systems use a self-hosted runner or AWS SSM. If you need SSH open to the world during the practice, remember to delete the instance when done.

Note: if you open SSH to `0.0.0.0/0` so GitHub can connect, the "My IP" rule must be replaced by it. Keep password login disabled (the Ubuntu AMI does this by default).

### 7.2 One-time server setup

From WSL (replace the path and IP):

```bash
mkdir -p ~/.ssh && cp /mnt/c/Users/YOU/Downloads/my-key.pem ~/.ssh/
chmod 400 ~/.ssh/my-key.pem          # SSH refuses keys others can read

# Copy the setup script to the server and run it
scp -i ~/.ssh/my-key.pem deploy/setup-server.sh ubuntu@EC2_PUBLIC_IP:~
ssh -i ~/.ssh/my-key.pem ubuntu@EC2_PUBLIC_IP "bash setup-server.sh"
```

The script installs Nginx and Python, creates `/var/www/python-app`, installs the **systemd** service (runs Gunicorn, restarts on crash, starts at boot) and the **Nginx** reverse proxy (port 80 to Gunicorn on 127.0.0.1:8000).

### 7.3 Collect the secret values

Run these in WSL:

```bash
# Host key of the server (lets GitHub verify it is talking to YOUR server)
ssh-keyscan -t ed25519 EC2_PUBLIC_IP

# Private key content (copy everything, including BEGIN/END lines)
cat ~/.ssh/my-key.pem
```

### 7.4 Add GitHub secrets and the enable switch

Repo > **Settings > Secrets and variables > Actions**.

**Secrets** (tab "Secrets" > New repository secret):

| Name | Value |
|---|---|
| `EC2_HOST` | The EC2 public IPv4 address, e.g. `203.0.113.25` |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Full contents of the `.pem` private key |
| `EC2_KNOWN_HOSTS` | Output line of `ssh-keyscan -t ed25519 EC2_PUBLIC_IP` |

**Variable** (tab "Variables" > New repository variable):

| Name | Value |
|---|---|
| `DEPLOY_ENABLED` | `true` |

Also create the **Environment** named `production` (Settings > Environments > New environment). Optionally add yourself as a required reviewer if you want a manual approval before each deploy.

Never commit the `.pem` file or paste these values into code. `.gitignore` already blocks `*.pem`.

> If you stop or restart the EC2 instance it may get a new public IP (unless you attach an Elastic IP). Update `EC2_HOST` and `EC2_KNOWN_HOSTS` when it changes.

### 7.5 Deploy

```bash
git commit --allow-empty -m "Trigger deploy"
git push
```

In the Actions tab the **Deploy to EC2** job now runs after the tests: it copies `app.py` and `requirements.txt` to `/var/www/python-app`, builds the virtual environment, installs dependencies, restarts the service, and finally calls `/health` on the public IP.

### 7.6 Verify the deployed app

```bash
curl http://EC2_PUBLIC_IP/health        # {"status":"ok"}
```

Open `http://EC2_PUBLIC_IP` in a browser (use `http://`, not `https://`).

On the server you can also check:

```bash
ssh -i ~/.ssh/my-key.pem ubuntu@EC2_PUBLIC_IP
sudo systemctl status python-app        # should say active (running)
sudo journalctl -u python-app -n 50     # app logs
sudo systemctl status nginx
sudo reboot                             # then confirm the site comes back by itself
```

Pushing a new commit to `main` redeploys automatically.

### 7.7 Turn deployment off

Set the variable `DEPLOY_ENABLED` to `false` (or delete it). CI keeps running; deploy is skipped. When finished practicing, terminate the EC2 instance to avoid charges.

---

## 8. Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| Workflow does not appear in Actions | File must be exactly `.github/workflows/ci-cd.yml` and pushed to GitHub. Check the YAML indentation. |
| `ModuleNotFoundError: No module named 'app'` in pytest | Run `python -m pytest` (not bare `pytest`) from the project root. |
| `No matching distribution found` | A version in `requirements.txt` is invalid for that Python version. Install locally to reproduce. |
| Docker build job fails | Read the failing step. Check the `Dockerfile` paths and that `requirements.txt` exists. |
| Deploy job shows "skipped" | Expected on pull requests, on other branches, or if `DEPLOY_ENABLED` is not exactly `true`. |
| `Permission denied (publickey)` | `EC2_SSH_KEY` is incomplete (missing BEGIN/END lines) or `EC2_USER` is wrong (Ubuntu AMI user is `ubuntu`). |
| `Host key verification failed` | `EC2_KNOWN_HOSTS` is missing or for a different IP. Re-run `ssh-keyscan`. |
| `Connection timed out` | Security group does not allow SSH (22) from the runner, or `EC2_HOST` is wrong or the instance is stopped. |
| `rsync: ... Permission denied` on `/var/www/python-app` | `setup-server.sh` was not run, or the folder is not owned by the `ubuntu` user. |
| Browser shows "502 Bad Gateway" | Gunicorn is not running. On the server run `sudo systemctl status python-app` and `sudo journalctl -u python-app -n 50`. |
| Browser cannot connect at all | Security group lacks HTTP (80) rule, or you used `https://`. |
| Browser shows "Welcome to nginx" | The default Nginx site is still enabled. Re-run `setup-server.sh`. |
| Final health check fails but service is active | Wait a few seconds and run `curl http://EC2_PUBLIC_IP/health`. Check `sudo nginx -t`. |

Useful commands: `git status`, `git log --oneline`, `sudo nginx -t` (validate Nginx config), `sudo systemctl daemon-reload` (after editing a service file).
