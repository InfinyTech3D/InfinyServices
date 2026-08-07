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
    "VirtualXRay",
    "ImagingUS",
    "SofaVerseAPI",
    "SofaHaplyRobotics",
]

REPOSITORIES_SOFA_PLUGINS = [
    "CGALPlugin",
    "Elasticity",
    "BeamAdapter",
    "SofaSkeletonPlugin",
    "SOFA.VTK",
    "ModelOrderReduction",
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

REPOSITORIES_PROJECTS = [
    "SofaLnRobotics",
    "DigitalTwin",
    "SofaUE5-Renderer",
]

REPOSITORIES = [REPOSITORIES_PLUGINS, REPOSITORIES_SOFA_PLUGINS, REPOSITORIES_UNITY, REPOSITORIES_PROJECTS]
SECTION_NAMES = ["IT3D plugins", "SOFA forked plugins", "Unity repositories", "Projects repositories"]
SECTION_NBR_PR = [0, 0, 0, 0]
TOTAL_NBR_PR = 0

TOKEN = os.environ.get("GITHUB_TOKEN")

headers = {
    "Authorization": f"token  {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# CI workflow filename used in each repository
WORKFLOW_FILE = "ci.yml"


def status_run_color(conclusion):
    if conclusion == "success":
        return "#2ecc71"   # green
    elif conclusion == "failure":
        return "#e74c3c"   # red
    elif conclusion == "N/A":
        return "#e74c3c"   # red
    elif conclusion == "API request failed":
        return "#e74c3c"   # red
    elif conclusion == "No workflow runs found":
        return "#979797"   # gray
    else:
        return "#f39c12"   # orange
    

def status_label_color(label):
    label = label.lower().strip()
    if "to review" in label:
        return "#006eff"   # blue
    elif "wip" in label:
        return "#b16a00"   # orange
    elif "ready" in label:
        return "#00960c"   # green
    else:
        return "#444444"   # gray


def pr_background(status_label, run_status):
    status_label = status_label.lower()

    if "status wip" in status_label:
        return "#d9d9d9"      # gray

    elif "status to review" in status_label:
        if run_status == "success":
            return "#9fd4ff"  # blue
        elif run_status == "failure":
            return "#ffb3b3"  # red
        else:
            return "#ffd27f"  # orange

    return "white"


print("===== Dashboard Generation Started =====")
print("Organization:", ORG)
print("Repositories:", REPOSITORIES)
print("Token available:", TOKEN is not None)

allrows = []
cptSection = 0
for repo_list in REPOSITORIES:
    rows = []
    nbrPR = 0
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
                    "url": pr["html_url"],
                    "author": pr["user"]["login"],
                    "labels": [label["name"] for label in pr["labels"]]
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
                    "date": datetime.strptime(
                        run["created_at"],
                        "%Y-%m-%dT%H:%M:%SZ"
                    ).strftime("%Y-%m-%d %H:%M:%S")
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
            run = runs_by_branch.get(branch)

            # Get pr: status
            for label in pr["labels"]:
                if label.startswith("pr: status"):
                    status_label = label
                    break

            if run:
                run_status = run["status"]
                run_conclusion = run["conclusion"]
                run_url = run["html_url"]
                run_date = datetime.strptime(
                    run["created_at"],
                    "%Y-%m-%dT%H:%M:%SZ"
                ).strftime("%Y-%m-%d %H:%M:%S")
            else:
                # No recent workflow run found
                run_status = "Unknown"
                run_conclusion = "No workflow runs found"
                run_url = "#"
                run_date = "None"

            rows.append({
                    "repo": repo,
                    "repo_link": pr["url"],
                    "branch": branch,
                    "is_pr": True,
                    "title": pr["title"],
                    "pr_number": pr["number"],
                    "author": pr["author"],
                    "pr_status_label": status_label,
                    "status": run_status,
                    "conclusion": run_conclusion,
                    "url": run_url,
                    "date": run_date
                })
            
            nbrPR += 1
    
    SECTION_NBR_PR[cptSection] = nbrPR
    TOTAL_NBR_PR += nbrPR
    cptSection += 1

    for r in rows:
        print("ROW:", r)

    
    allrows.append(rows)


print("\n===== Generating HTML =====")

os.makedirs("public", exist_ok=True)

html = f"""
<html>
<head>
<title>CI Dashboard</title>
<style>
table {{ border-collapse: collapse; }}
td, th {{ border:1px solid #999; padding:8px; }}
</style>
</head>
<body>
<h1>CI Dashboard v8 - Last update: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} | Total Nbr open PR: {TOTAL_NBR_PR}</h1>

"""
cptSection = 0
for section in allrows:
    html += f"""
        <h2>{SECTION_NAMES[cptSection]}: Nbr open PR: {SECTION_NBR_PR[cptSection]}</h2>
        <table>
        <tr>
        <th>Repository</th>
        <th>Branch</th>
        <th>Label Status</th>
        <th>Author</th>

        <th>Last CI run</th>
        <th>Run Status</th>
        <th>Run Conclusion</th>
        </tr>
    """

    for row in section:
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

        # Get all info from the arrays and prepare texts for the table raw
        if row["is_pr"]:
            repo_title = f" - PR #{row['pr_number']}"
            branch_display = f'PR #{row["pr_number"]}: {row["title"]}'
            author = row["author"]
            status_label = row["pr_status_label"]
            css_class = "pr"
        else:
            repo_title = f'<b>{row["repo"]}</b>'
            branch_display = f'<b>{row["branch"]}</b>'
            status_label = "NA"
            author = "NA"
            css_class = "main"

        # Compute colors for text and bg
        color_run = status_run_color(conclusion)
        color_label = status_label_color(status_label)

        if row["is_pr"]:
            bg_color_repo = pr_background(status_label, conclusion)
            bg_color_raw = "white"
        else:
            if conclusion == "failure":
                bg_color_raw = "#bd6969"   # Broken main branch
            elif conclusion == "success":
                bg_color_raw = "#79af68"   # Healthy CI
            else:
                bg_color_raw = "#A7A7A7"   # Healthy or no CI
            bg_color_repo = bg_color_raw


        html += f"""
            <tr>
            <td style="background-color:{bg_color_repo};">{repo_title}</td>
            <td style="background-color:{bg_color_raw}";><a href="{repo_link}" target="_blank">{branch_display}</a></td>
            <td style="background-color:{bg_color_raw}; color:{color_label}; font-weight:bold;">{status_label}</td>
            <td style="background-color:{bg_color_raw};">{author}</td>

            <td><a href="{workflow_link}" target="_blank">{updated}</a></td>
            <td style="color:{color_run}; font-weight:bold;">{status}</td>
            <td style="color:{color_run}; font-weight:bold;">{conclusion}</td>
            </tr>
        """
    html += "</table>"
    cptSection += 1

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
