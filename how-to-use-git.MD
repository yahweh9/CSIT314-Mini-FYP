# CSIT314-Mini-FYP
CSIT314 Software Methodology 

# 🧭 GitHub Guide: How to Clone and Pull a Repository

This guide will help **new developers** understand how to **clone** (download) and **pull** (update) a GitHub repository to their local computer.

---

## 🪄 What You’ll Need
Before starting, make sure you have:
- ✅ A **GitHub account** ([https://github.com](https://github.com))
- ✅ **Git** installed on your computer  
  - Check if Git is installed:
    ```bash
    git --version
    ```
  - If not installed, download it from [https://git-scm.com/downloads](https://git-scm.com/downloads)

---

## 🧰 Step 1: Find the Repository URL

1. Go to the repository page on GitHub.
2. Click the green **Code** button.
3. Copy the **HTTPS** link (recommended for beginners).

Example: https://github.com/yahweh9/CSIT314-Mini-FYP



---

## 💾 Step 2: Clone (Download) the Repository

Cloning means making a local copy of the repository on your computer.

1. Open your terminal (Mac/Linux) or Git Bash (Windows).
2. Navigate to the folder where you want to save the project:
   ```bash
   cd ~/Desktop

3. git clone https://github.com/yahweh9/CSIT314-Mini-FYP

4. cd repository-name
✅ You now have a full copy of the project locally!


## 🔄 Step 3: Pull (Update) the Repository
If the repository changes on GitHub, you can pull updates to keep your local copy current.

1. Open your project folder in Terminal:
   cd ~/Desktop/repository-name

2. Run the pull command:
   git pull origin main

origin = the remote GitHub repository
main = the default branch (sometimes master)
If you see Already up to date, it means your local copy matches GitHub.


## 🌿 Step 4: Checking Your Branch
To check which branch you are on:

git branch

If you see:
* main
that means you are on the main branch.

## 🚀 Step 5: Push Changes to GitHub

1. Check what’s changed
  git status

2. Stage your changes
  To add all changed files:
    git add .
Or to add specific files:
  git add filename.txt

3. Commit your changes
  git commit -m "Describe what you changed"

4. Push to GitHub
  git push origin main



