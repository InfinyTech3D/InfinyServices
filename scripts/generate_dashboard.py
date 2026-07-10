import os
import requests
from datetime import datetime

ORG = "InfinyTech3D"

REPOSITORIES_PLUGINS = [
    "InfinyToolkit",
    "InfinyPrefabs",
    "CollisionAlgorithm",
    "ConstraintGeometry",
    "NeedleInsertion",
    "MeshRefinement",
    "Tearing",
    "SofaHaplyRobotics",
    "VirtualXRay",
    "ImagingUS",
    "SofaVerseAPI",
]

REPOSITORIES_UNITY = [
    "SofaUnity",
    "SofaUnityXR",
    "SofaUnity_Modules",
    "SofaUnity_Surgery",
    "SofaUnity_Environments",
    "SurgiViz4D",
    "SurgiViz4DServerMDB",
]

REPOSITORIES_SOFA_PLUGINS = [
    "CGALPlugin",
    "Elasticity",
    "BeamAdapter",
    "SofaSkeletonPlugin",
    "SOFA.VTK",
]

REPOSITORIES_PROJECTS = [
    "SofaLnRobotics",
    "DigitalTwin",
    "SofaUE5-Renderer",
]

REPOSITORIES = [REPOSITORIES_PLUGINS, REPOSITORIES_UNITY, REPOSITORIES_SOFA_PLUGINS, REPOSITORIES_PROJECTS]



TOKEN = os.environ.get("GITHUB_TOKEN")

headers = {
    "Authorization": f"token  {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# CI workflow filename used in each repository
WORKFLOW_FILE = "ci.yml"


def status_color(conclusion):
    if conclusion == "success":
        return "#2ecc71"   # green
    elif conclusion == "failure":
        return "#e74c3c"   # red
    elif conclusion == "N/A":
        return "#e74c3c"   # red
    elif conclusion == "API request failed":
        return "#e74c3c"   # red
    else:
        return "#f39c12"   # orange

print("===== Dashboard Generation Started =====")
print("Organization:", ORG)
print("Repositories:", REPOSITORIES)
print("Token available:", TOKEN is not None)

allrows = []

for repo_list in REPOSITORIES:
    rows = []
    for repo in repo_list:

        print("\n--------------------------------")
        print("Processing repository:", repo)

        repo_link = f"https://github.com/{ORG}/{repo}"
        url = f"https://api.github.com/repos/{ORG}/{repo}/actions/runs?per_page=50"
        #f"https://api.github.com/repos/{ORG}/{repo}/actions/workflows/{WORKFLOW_FILE}/runs?per_page=50"
        #url = f"https://api.github.com/repos/{ORG}/{repo}/actions/runs?event=push&status=completed&per_page=1"

        response = requests.get(url, headers=headers)
        
        print("Querying API:", url)
        print("HTTP status:", response.status_code)
        print("Auth test status:", response.status_code)
        print("Authenticated user:", response.json().get("login"))

        auth_test = requests.get("https://api.github.com/user", headers=headers)
        print("Auth test status:", auth_test.status_code)
        print("Authenticated user:", auth_test.json().get("login"))
        
        if response.status_code != 200:
            print("Failed to fetch repository data")
            rows.append({
                    "repo": repo,
                    "repo_link": repo_link,
                    "branch": "#",
                    "is_pr": False,
                    "title": "N/A",
                    "status": "Error",
                    "conclusion": "API request failed",
                    "url": "#",
                    "date": "#"
                })
            continue

        data = response.json()
        runs = data.get("workflow_runs", [])
        
        print("Total runs reported by API:", data.get("total_count"))
        print("Number of runs parsed:", len(runs))

        # -----------------------------
        # Get open pull requests
        # -----------------------------
        
        pulls_url = f"https://api.github.com/repos/{ORG}/{repo}/pulls?state=open"   
        print("Querying open PRs:", pulls_url)
        
        pulls_response = requests.get(pulls_url, headers=headers)
        #open_prs = set()
        open_prs = []
        if pulls_response.status_code == 200:
            pulls_data = pulls_response.json()
            for pr in pulls_response.json():
                open_prs.append({
                    "number": pr["number"],
                    "branch": pr["head"]["ref"],
                    "title": pr["title"],
                    "url": pr["html_url"]
                })

        print("Open PR branches:", open_prs)

        
        # -----------------------------
        # Select latest runs
        # -----------------------------
        main_run = None
        runs_by_branch = {}
        for run in runs:
            branch = run.get("head_branch")
            event = run.get("event")

            # ---- main/master branch ----
            if branch in ["main", "master"] and main_run is None:
                main_run = run
                continue
            
            if branch not in runs_by_branch:
                runs_by_branch[branch] = run
        
        # ------------------------
        # MAIN BRANCH RUN
        # ------------------------
        if main_run:
            print("Add main run")
            rows.append({
                    "repo": repo,
                    "repo_link": repo_link,
                    "branch": main_run["head_branch"],
                    "is_pr": False,
                    "title": "",
                    "status": main_run["status"],
                    "conclusion": main_run["conclusion"],
                    "url": run["html_url"],
                    "date": run["created_at"]
                })
        else:
            print("No main/master run found")
            rows.append({
                    "repo": repo,
                    "repo_link": repo_link,
                    "branch": "main/master",
                    "is_pr": False,
                    "title": "",
                    "status": "Unknown",
                    "conclusion": "No workflow runs found",
                    "url": "#",
                    "date": "None"
                })

        # -----------------------------
        # Add PR rows
        # -----------------------------
        for pr in open_prs:
            branch = pr["branch"]
            pr_title = pr["title"]
            pr_number = pr["number"]
            repo_link = pr["url"]

            run = runs_by_branch.get(branch)

            if run:
                status = run["status"]
                conclusion = run["conclusion"]
                url = run["html_url"]
                date = run["created_at"]
            else:
                # No recent workflow run found
                status = "Unknown"
                conclusion = "No workflow runs found"
                url = "#"
                date = "None"

            rows.append({
                    "repo": repo,
                    "repo_link": repo_link,
                    "branch": branch,
                    "is_pr": True,
                    "title": pr_title,
                    "pr_number": pr_number,
                    "status": status,
                    "conclusion": conclusion,
                    "url": url,
                    "date": date
                })
    
        print("Number of rows selected:", len(rows))

    
    for r in rows:
        print("ROW:", r)


        # run = runs[0]
        # status = run["status"]
        # conclusion = run["conclusion"]
        # updated = run["updated_at"]
        # workflow_link = run["html_url"]
        # branch = run["head_branch"]

        # print("Latest run status:", status)
        # print("Latest run conclusion:", conclusion)
        # print("Updated at:", updated)
        # print(f"Repository: {repo_link}")
        # print(f"Workflow: {workflow_link}")

        # rows.append((repo, repo_link, branch, status, conclusion, updated, workflow_link))
    
    allrows.append(rows)


print("\n===== Generating HTML =====")

os.makedirs("public", exist_ok=True)

html = """
<html>
<head>
<title>CI Dashboard</title>
<style>
table {{ border-collapse: collapse; }}
td, th {{ border:1px solid #999; padding:8px; }}
</style>
</head>
<body>
<h1>CI Dashboard V6</h1>
<p>Last update: {}</p>
<table>
<tr>
<th>Repository</th>
<th>Branch</th>
<th>Status</th>
<th>Conclusion</th>
<th>Last Update</th>
<th>CI Run</th>
</tr>
""".format(datetime.utcnow())

for section in allrows:
    for row in section:
        repo_title = row["repo"]
        repo_link = row["repo_link"]
        status = row["status"]
        conclusion = row["conclusion"]
        updated = row["date"]
        workflow_link = row["url"]
        #branch_display = row["branch"]

        css = ""
        if conclusion == "success":
            css = "success"
        elif conclusion == "failure":
            css = "failure"

        color = status_color(conclusion)
        
        if row["is_pr"]:
            repo_title = f" - {row['repo']} (PR #{row['pr_number']})"
            branch_display = f'PR #{row["pr_number"]}: {row["title"]}'
            css_class = "pr"
        else:
            branch_display = f'<b>{row["branch"]}</b>'
            css_class = "main"

        html += f"""
<tr>
<td><a href="{repo_link}" target="_blank">{repo_title}</a></td>
<td>{branch_display}</td>
<td style="color:{color}; font-weight:bold;">{status}</td>
<td style="color:{color}; font-weight:bold;">{conclusion}</td>
<td>{updated}</td>
<td><a href="{workflow_link}" target="_blank">{workflow_link}</a></td>
</tr>

"""

html += """
</table>
</body>
</html>
"""

with open("public/index.html", "w") as f:
    f.write(html)

print("HTML dashboard written to public/index.html")
print("HTML preview:")
print(html[:500])
print("===== Dashboard Generation Completed =====")
