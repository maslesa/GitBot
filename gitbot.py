import textwrap
import requests
import openai
import datetime
from tabulate import tabulate

#CONFIGS
OPENAI_API = "" #your openai
USERNAME = "" #your github username
TOKEN = "" #your github token
headers = {"Authorization": f"token {TOKEN}"}
openai.api_key = OPENAI_API

#CONSTANTS
AVERAGE_NUM_OF_REPOS_PER_YEAR = 20
YEAR = datetime.datetime.now().year
MONTH = datetime.datetime.now().month
MAX_TOKENS = 300

def count_repos():
    URL = f"https://api.github.com/users/{USERNAME}/repos"
    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        table_data = []
        num_of_repos = 0

        for repo in repos:
            date = repo['created_at']
            if date[:4] == str(YEAR):
                table_data.append([repo['name'], date])
                num_of_repos += 1

        print(tabulate(table_data, headers=["Repository Name", "Created At"], tablefmt="pretty"))
        return num_of_repos
    else:
        print(f"Error: {response.status_code} - {response.text}")
def list_all_repos():
    URL = f"https://api.github.com/users/{USERNAME}/repos"
    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        repos = response.json()
        table_data = []
        for repo in repos:
            table_data.append([repo['name']])
        print(tabulate(table_data, headers=["Repositories"], tablefmt="pretty"))
    else:
        print(f"Error: {response.status_code} - {response.text}")
def check_commits():
    URL = f"https://api.github.com/users/{USERNAME}/events"
    response = requests.get(URL, headers=headers)
    total_commits = 0
    if response.status_code == 200:
        events = response.json()
        table_data = []
        for event in events:
            table_data.append([event['repo']['name'][len(USERNAME)+1:], event['type'], event['created_at']])
        print(tabulate(table_data, headers=["Repository Name", "Event Type", "Created At"], tablefmt="pretty"))
    else:
        print(f"Error: {response.status_code} - {response.text}")


#AI
def ask_ai(text):
    try:
        response_ai = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are GitBot, a helpful assistant that helps developers track and analyze activity on their GitHub accounts."},
                {"role": "user", "content": text}
            ]
        )
        return response_ai['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    print('###GITBOT###\nIf you need help, enter `gitbot --help`\n')
    ai_answer = ""
    while True:
        answer = input('$: ')
        if answer == 'gitbot --help':
            print('\n#repository commands:')
            print('[check repository activity]: `repo --activity`')
            print('[list all repositories]: `repo --all` or `repo -a`')

            print('\n#commmits commands:')
            print('[check all commits activity]: `commits --activity`')
            print('[check commits activity for specific repo]: `commits --activity [repository name]`')

            print('\n#gitbot ai:')
            print('[make README.md file]: `readme make [repository name]`')

            print('\n[exit]: gitbot /exit\n')

        elif answer == 'repo --activity':
            num_of_repos_this_year = count_repos()
            print('Do you want advice[yes/no]?')
            while True:
                choice = input('>>')
                if choice == "yes":
                    ai_answer = f"""I have {num_of_repos_this_year} projects on my GitHub for this year ({YEAR}), 
                                    and month ({MONTH}) and average is {AVERAGE_NUM_OF_REPOS_PER_YEAR} per year.
                                    Give me some advice what should I do and what type of projects should I build.
                                    Use {MAX_TOKENS} tokens max and do not ask answer at the end."""
                    ai_response = ask_ai(ai_answer)
                    print(textwrap.fill(ai_response, width=50))
                    break
                elif choice == "no":
                    break
                else:
                    print('unknown word `choice`, please enter `yes` or `no`')

        elif answer in ('repo --all', 'repo -a'):
            list_all_repos()

        elif answer == 'commits --activity':
            check_commits()

        elif answer == 'gitbot /exit':
            print('gitbot canceling...')
            print('gitbot canceled')
            break
        else:
            print('No such a command like `' + answer + '`')

if __name__ == "__main__":
    main()