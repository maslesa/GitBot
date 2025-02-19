import textwrap
import time
import os
import requests
import openai
import datetime
import base64
import sys
from tabulate import tabulate


def load_configs():
    with open("config.txt", "r") as config_file:
        lines = config_file.read().splitlines()
        openai_api = lines[0].split('=')[1] if len(lines[0]) > 0 else ""
        git_token = lines[1].split('=')[1] if len(lines[1]) > 0 else ""
        username = lines[2].split('=')[1] if len(lines[2]) > 0 else ""

        return openai_api, git_token, username


# CONFIGS
OPENAI_API, TOKEN, USERNAME = load_configs()
headers = {"Authorization": f"token {TOKEN}"}
openai.api_key = OPENAI_API

# CONSTANTS
AVERAGE_NUM_OF_REPOS_PER_YEAR = 20
YEAR = datetime.datetime.now().year
MONTH = datetime.datetime.now().month
MAX_TOKENS = 300


def typing(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def count_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        table_data = []
        num_of_repos = 0

        for repo in repos:
            date = repo['created_at']
            table_data.append([repo['name'], date, repo['updated_at']])
            num_of_repos += 1

        print(tabulate(table_data, headers=["Repository Name", "Created At", "Last update"], tablefmt="pretty"))
        return num_of_repos
    else:
        print(f"Error: {response.status_code} - {response.text}")


def list_all_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        table_data = []
        for repo in repos:
            table_data.append([repo['name']])
        print(tabulate(table_data, headers=["Repositories"], tablefmt="pretty"))
        print()
    else:
        print(f"Error: {response.status_code} - {response.text}")


def check_commits():
    url = f"https://api.github.com/users/{USERNAME}/events"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        events = response.json()
        table_data = []
        for event in events:
            table_data.append([event['repo']['name'][len(USERNAME) + 1:], event['type'], event['created_at']])
        print(tabulate(table_data, headers=["Repository Name", "Event Type", "Created At"], tablefmt="pretty"))
        print()
    else:
        print(f"Error: {response.status_code} - {response.text}")


def check_commits_repo(repo_name):
    url = f"https://api.github.com/users/{USERNAME}/events"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        events = response.json()
        table_data = []
        for event in events:
            if event['repo']['name'][len(USERNAME) + 1:] == repo_name:
                table_data.append([event['repo']['name'][len(USERNAME) + 1:], event['type'], event['created_at']])
        print(tabulate(table_data, headers=["Repository Name", "Event Type", "Created At"], tablefmt="pretty"))
    else:
        print(f"Error: {response.status_code} - {response.text}")


def get_all_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos"
    response = requests.get(url, headers=headers)
    list_of_repos = []
    if response.status_code == 200:
        repos = response.json()
        for repo in repos:
            list_of_repos.append(repo['name'])
        return list_of_repos
    else:
        print(f"Error: {response.status_code} - {response.text}")


# AI
def ask_ai(text):
    try:
        response_ai = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are GitBot, a helpful assistant that helps developers "
                            "track and analyze activity on their GitHub accounts."},
                {"role": "user", "content": text}
            ]
        )
        return response_ai['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error: {e}"


def generate_readme(description, repo):
    answer_ai = f"""Generate a well-structured README.md file for a GitHub project 
                    based on this description: {description}.
                    This project is on https://github.com/{USERNAME}/{repo} (do not put this link
                    in answer, this is only for you to check whole project to write better README.md file)
                    Include sections like Introduction, Features and Usage.
                    Do not ask question at the end of the answer!
    """
    response_ai = ask_ai(answer_ai)
    return response_ai


def upload_readme(readme_text, repo):
    url = f"https://api.github.com/repos/{USERNAME}/{repo}/contents/README.md"
    response = requests.get(url, headers=headers)

    data = {
        "message": "Add README.md",
        "content": base64.b64encode(readme_text.encode()).decode(),
        "branch": "main"
    }

    if response.status_code == 200:  # readme exists
        sha = response.json().get("sha")
        data["message"] = "Update README.md"
        data["sha"] = sha

    response = requests.put(url, json=data, headers=headers)

    if response.status_code in [200, 201]:
        print(f"README.md successfully {'updated' if 'sha' in data else 'created'} in {repo}.")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def save_projects(ai_answer):
    with open('projects.txt', 'a') as file:
        file.write(ai_answer + '\n\n')
        print('\nprojects has been saved successfully in `projects.txt`')
        file.close()


def main():
    print('###GITBOT###\nIf you need help, enter `gitbot --help`\n')
    while True:
        try:
            answer = input('$: ')

            if answer == "cls":
                os.system("cls" if os.name == "nt" else "clear")
                continue

            if answer == 'gitbot --help':
                print('\n###GITBOT HELP MENU###')
                print('\n#repository commands:')
                print('[check repository activity]: `repo --activity`')
                print('[list all repositories]: `repo --all` or `repo -a`')

                print('\n#commmits commands:')
                print('[check all commits activity]: `commits --activity`')
                print('[check commits activity for specific repo]: `commits --activity --repo=[repository name]`')

                print('\n#gitbot ai helper:')
                print('[make/update README.md file]: `readme make --repo=[repository name]`')
                print('[help for choosing next projects]: projects --help')
                print('[open saved projects]: projects --view')

                print('\n[exit]: gitbot /exit\n')

            elif answer == 'repo --activity':
                num_of_repos_this_year = count_repos()
                print('\nDo you want advice about new projects[yes/no]?')
                while True:
                    choice = input('>>')
                    if choice == "yes":
                        ai_answer = f"""I have {num_of_repos_this_year} projects on my GitHub for this year ({YEAR}), 
                                        and month ({MONTH}) and average is {AVERAGE_NUM_OF_REPOS_PER_YEAR} per year.
                                        Give me some advice what should I do and what type of projects should I build.
                                        Use {MAX_TOKENS} tokens max and do not ask answer at the end."""
                        ai_response = ask_ai(ai_answer)
                        typing(textwrap.fill(ai_response, width=100))
                        print()
                        break
                    elif choice == "no":
                        print()
                        break
                    else:
                        print(f'unknown word `{choice}`, please enter `yes` or `no`')

            elif answer in ('repo --all', 'repo -a'):
                list_all_repos()

            elif answer == 'commits --activity':
                check_commits()

            elif answer.startswith('commits --activity ') and answer.find('--repo='):
                repo_name = answer.split("--repo=")[1]
                check_commits_repo(repo_name)

            elif answer == 'projects --help':
                all_repos = get_all_repos()
                future_projects_themes = input('Enter some themes for future projects you would like to make:')
                print('Select difficulty for next projects [enter a number]:\n[1] Easy\n[2] Medium\n[3] Hard')
                while True:
                    difficulty_level = input('>>')
                    if difficulty_level == '1':
                        difficulty = 'Easy'
                        break
                    elif difficulty_level == '2':
                        difficulty = 'Medium'
                        break
                    elif difficulty_level == '3':
                        difficulty = 'Hard'
                        break
                    else:
                        print(f'Incorrect input `{difficulty_level}`')
                typing('searching for projects...\n')
                ai_answer = f"""I made this projects: {all_repos}. Help me to choose new ones to make and put them
                                on my GitHub account. I would like to make projects with themes 
                                like {future_projects_themes} and the difficulty of this projects have to be on
                                difficulty level: {difficulty}. Look for previous projects I made and projects I
                                would like to make and tell me ten new projects I can make and put on my GitHub.
                                Do not ask question at the end of answer!
                """
                ai_response = ask_ai(ai_answer)
                typing(ai_response)
                while True:
                    save_choice = input('\nDo you want to save this answer?[yes/no]')
                    if save_choice == 'yes':
                        save_projects(ai_response)
                        break
                    elif save_choice == 'no':
                        break
                    else:
                        print(f'unknown word `{save_choice}`, please enter `yes` or `no`')

            elif answer == 'projects --view':
                # WARNING: when it's opened like an .exe file, it can't find projects.txt file
                base_path = os.path.dirname(os.path.abspath(__file__))

                file_path = os.path.join(base_path, "dist", "projects.txt")
                if os.path.exists(file_path):
                    os.startfile(file_path)
                else:
                    print("File not found! Check the path:", file_path)

            elif answer.startswith('readme make --repo='):
                repo = answer.split('--repo=')[1]
                all_repos = get_all_repos()
                if repo not in all_repos:
                    print('you don\'t have repository with that name.')
                    continue
                print('Write description for your project:')
                description = input('>> ')
                while True:
                    readme_text = generate_readme(description, repo)
                    print('\nREADME.md file:')
                    print(readme_text)
                    choice = input('\nDo you want to upload this README.md file[yes/no] [stop(deny function)]? ')
                    if choice == 'yes':
                        upload_readme(readme_text, repo)
                        break
                    elif choice == 'no':
                        print('generating new README.md file...\n')
                        continue
                    elif choice == 'stop':
                        print('generating README.md file stopped!\n')
                        break

            elif answer == '':
                continue

            elif answer == 'gitbot /exit':
                typing('gitbot canceling...')
                typing('gitbot canceled')
                break

            else:
                print('No such a command like `' + answer + '`')

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
