import json
from bots.loaders.git import git_review
#from bots.loaders.outlook import get_email_summary


if __name__ == "__main__":
    
    git_test = git_review()

    response = git_test._run(query="Tell me about this repo", giturl="https://github.com/zekis/chad")

    print(response)