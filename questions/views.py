from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.http import require_POST
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse


POPULAR_TAGS = [
    'perl', 'python', 'javascript', 'java', 'csharp', 'php',
    'html', 'css', 'react', 'vue', 'angular', 'nodejs', 
    'sql', 'mongodb', 'docker', 'kubernetes', 'git', 'aws'
]

BEST_MEMBERS = [
    'Mr. Freeman', 'Dr. House', 'Bender', 'Queen Victoria',
    'Dr. Who', 'John Doe', 'Alice Cooper', 'Bob Smith'
]

QUESTIONS = [
        {
        'id': 1,
        'profile_picture': 'profile-picture.png',
        'votes': 5,
        'title': 'How to build a mean peak?',
        'url': 'questions/1',
        'description': 'Lorem ipsum dolor sit amet consectetur adipisicing elit. Ullam nulla laboriosam, tempore libero mollitia sunt omnis odit tenetur totam quam veritatis, sint atque facere laborum aperiam sapiente culpa dolorem vero.',
        'answers_count': 10,
        'tags': [
            {'name': 'bender', 'url': 'questions/tag/bender'},
            {'name': 'black-jack', 'url': 'questions/tag/black-jack'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 8,
                'text': 'You need to use the Fourier transform to analyze the frequency components of your signal. Then apply a peak detection algorithm to identify the mean peak.',
                'is_correct': True,
                'author': 'Dr. House',
                'created_at': '2024-01-15 14:30:00'
            },
            {
                'id': 2,
                'profile_picture': 'profile-picture.png',
                'votes': 3,
                'text': 'I would recommend using scipy.signal.find_peaks() function in Python. It has parameters for height, distance, and prominence that can help you find mean peaks.',
                'is_correct': False,
                'author': 'Mr. Freeman',
                'created_at': '2024-01-15 16:45:00'
            },
        ]
    },
    {
        'id': 2,
        'profile_picture': 'profile-picture.png',
        'votes': 12,
        'title': 'How to center a div with CSS?',
        'url': 'questions/2',
        'description': 'I\'ve been trying to center a div for hours but nothing seems to work. I\'ve tried display: flex, margin: auto, but the div still won\'t center properly.',
        'answers_count': 7,
        'tags': [
            {'name': 'css', 'url': 'questions/tag/css'},
            {'name': 'html', 'url': 'questions/tag/html'},
            {'name': 'flexbox', 'url': 'questions/tag/flexbox'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 15,
                'text': 'Use flexbox: display: flex; justify-content: center; align-items: center; This will center your div both horizontally and vertically.',
                'is_correct': True,
                'author': 'CSS Master',
                'created_at': '2024-01-14 10:20:00'
            }
        ]
    },
    {
        'id': 3,
        'profile_picture': 'profile-picture.png',
        'votes': 8,
        'title': 'JavaScript async/await not working as expected',
        'url': 'questions/3',
        'description': 'My async function seems to be returning a promise instead of the actual value. I\'m using await but it\'s still not working correctly.',
        'answers_count': 4,
        'tags': [
            {'name': 'javascript', 'url': 'questions/tag/javascript'},
            {'name': 'async', 'url': 'questions/tag/async'},
            {'name': 'promises', 'url': 'questions/tag/promises'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 12,
                'text': 'Make sure you\'re using await inside an async function. Also, check if you\'re missing the async keyword in the function declaration.',
                'is_correct': True,
                'author': 'JS Expert',
                'created_at': '2024-01-13 08:15:00'
            }
        ]
    },
    {
        'id': 4,
        'profile_picture': 'profile-picture.png',
        'votes': 15,
        'title': 'Python list comprehension vs for loop performance',
        'url': 'questions/4',
        'description': 'Which is faster for large datasets - list comprehension or traditional for loops? I\'m working with datasets of over 1 million records and need optimal performance.',
        'answers_count': 11,
        'tags': [
            {'name': 'python', 'url': 'questions/tag/python'},
            {'name': 'performance', 'url': 'questions/tag/performance'},
            {'name': 'optimization', 'url': 'questions/tag/optimization'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 25,
                'text': 'List comprehensions are generally faster because they are optimized at the C level in Python. However, for very complex operations, a traditional loop might be more readable.',
                'is_correct': True,
                'author': 'Python Core Dev',
                'created_at': '2024-01-12 14:20:00'
            }
        ]
    },
    {
        'id': 5,
        'profile_picture': 'profile-picture.png',
        'votes': 3,
        'title': 'React hooks dependency array issue',
        'url': 'questions/5',
        'description': 'My useEffect hook keeps running in an infinite loop even though I\'ve specified the dependency array correctly. What could be causing this behavior?',
        'answers_count': 2,
        'tags': [
            {'name': 'react', 'url': 'questions/tag/react'},
            {'name': 'hooks', 'url': 'questions/tag/hooks'},
            {'name': 'useeffect', 'url': 'questions/tag/useeffect'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 10,
                'text': 'This usually happens when you have an object or array in the dependency array that gets recreated on every render. Use useMemo or useCallback to memoize the dependency.',
                'is_correct': True,
                'author': 'React Guru',
                'created_at': '2024-01-11 11:25:00'
            }
        ]
    },
    {
        'id': 6,
        'profile_picture': 'profile-picture.png',
        'votes': 9,
        'title': 'Database migration strategies for zero downtime',
        'url': 'questions/6',
        'description': 'What are the best practices for performing database migrations without causing downtime for users? Looking for strategies that have worked in production environments.',
        'answers_count': 6,
        'tags': [
            {'name': 'database', 'url': 'questions/tag/database'},
            {'name': 'migration', 'url': 'questions/tag/migration'},
            {'name': 'devops', 'url': 'questions/tag/devops'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 20,
                'text': 'Use blue-green deployment strategy. Have two identical environments. Migrate the standby environment, test it thoroughly, then switch traffic.',
                'is_correct': True,
                'author': 'DevOps Engineer',
                'created_at': '2024-01-10 09:15:00'
            }
        ]
    },
    {
        'id': 7,
        'profile_picture': 'profile-picture.png',
        'votes': 7,
        'title': 'Docker container keeps restarting randomly',
        'url': 'questions/7',
        'description': 'My Docker container restarts every few hours without any apparent reason. How can I debug this issue and prevent random restarts?',
        'answers_count': 5,
        'tags': [
            {'name': 'docker', 'url': 'questions/tag/docker'},
            {'name': 'containers', 'url': 'questions/tag/containers'},
            {'name': 'devops', 'url': 'questions/tag/devops'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 14,
                'text': 'Check the container logs using docker logs. The container might be running out of memory or hitting resource limits. Set proper memory limits and monitor resource usage.',
                'is_correct': True,
                'author': 'Docker Expert',
                'created_at': '2024-01-09 16:30:00'
            }
        ]
    },
    {
        'id': 8,
        'profile_picture': 'profile-picture.png',
        'votes': 11,
        'title': 'Best practices for REST API authentication',
        'url': 'questions/8',
        'description': 'What are the current best practices for implementing authentication in REST APIs? Should I use JWT, OAuth2, or session-based authentication?',
        'answers_count': 8,
        'tags': [
            {'name': 'api', 'url': 'questions/tag/api'},
            {'name': 'authentication', 'url': 'questions/tag/authentication'},
            {'name': 'security', 'url': 'questions/tag/security'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 18,
                'text': 'JWT is great for stateless authentication, but consider using refresh tokens for better security. OAuth2 is ideal for third-party authentication. Choose based on your use case.',
                'is_correct': True,
                'author': 'Security Pro',
                'created_at': '2024-01-08 14:20:00'
            }
        ]
    },
    {
        'id': 9,
        'profile_picture': 'profile-picture.png',
        'votes': 6,
        'title': 'Machine learning model overfitting',
        'url': 'questions/9',
        'description': 'My neural network model is achieving 99% accuracy on training data but only 60% on test data. How can I reduce overfitting?',
        'answers_count': 4,
        'tags': [
            {'name': 'machine-learning', 'url': 'questions/tag/machine-learning'},
            {'name': 'python', 'url': 'questions/tag/python'},
            {'name': 'tensorflow', 'url': 'questions/tag/tensorflow'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 12,
                'text': 'Try adding dropout layers, L2 regularization, early stopping, or increasing your training data. Also consider simplifying your model architecture.',
                'is_correct': True,
                'author': 'ML Engineer',
                'created_at': '2024-01-07 11:45:00'
            }
        ]
    },
    {
        'id': 10,
        'profile_picture': 'profile-picture.png',
        'votes': 14,
        'title': 'Git merge conflict resolution strategies',
        'url': 'questions/10',
        'description': 'What are the best strategies for resolving complex merge conflicts in Git, especially when multiple developers are working on the same files?',
        'answers_count': 9,
        'tags': [
            {'name': 'git', 'url': 'questions/tag/git'},
            {'name': 'version-control', 'url': 'questions/tag/version-control'},
            {'name': 'collaboration', 'url': 'questions/tag/collaboration'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 22,
                'text': 'Use a visual merge tool, communicate with team members, and consider using rebase instead of merge for cleaner history. Always test after resolving conflicts.',
                'is_correct': True,
                'author': 'Git Master',
                'created_at': '2024-01-06 09:30:00'
            }
        ]
    },
    {
        'id': 11,
        'profile_picture': 'profile-picture.png',
        'votes': 8,
        'title': 'Microservices vs Monolith architecture',
        'url': 'questions/11',
        'description': 'When should I choose microservices over a monolith architecture? What are the trade-offs and when does microservices become overkill?',
        'answers_count': 7,
        'tags': [
            {'name': 'architecture', 'url': 'questions/tag/architecture'},
            {'name': 'microservices', 'url': 'questions/tag/microservices'},
            {'name': 'system-design', 'url': 'questions/tag/system-design'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 16,
                'text': 'Start with a monolith until you have clear bounded contexts. Microservices add complexity - only use when you have multiple teams and need independent deployment.',
                'is_correct': True,
                'author': 'System Architect',
                'created_at': '2024-01-05 15:20:00'
            }
        ]
    },
    {
        'id': 12,
        'profile_picture': 'profile-picture.png',
        'votes': 5,
        'title': 'Redis cache invalidation patterns',
        'url': 'questions/12',
        'description': 'What are the best patterns for cache invalidation in Redis? I\'m having issues with stale data and race conditions.',
        'answers_count': 3,
        'tags': [
            {'name': 'redis', 'url': 'questions/tag/redis'},
            {'name': 'caching', 'url': 'questions/tag/caching'},
            {'name': 'performance', 'url': 'questions/tag/performance'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 11,
                'text': 'Use write-through caching, set appropriate TTL values, and consider using Redis pub/sub for cache invalidation across multiple instances.',
                'is_correct': True,
                'author': 'Cache Expert',
                'created_at': '2024-01-04 13:10:00'
            }
        ]
    },
    {
        'id': 13,
        'profile_picture': 'profile-picture.png',
        'votes': 9,
        'title': 'WebSocket vs Server-Sent Events',
        'url': 'questions/13',
        'description': 'When should I use WebSockets versus Server-Sent Events for real-time communication in a web application?',
        'answers_count': 6,
        'tags': [
            {'name': 'websocket', 'url': 'questions/tag/websocket'},
            {'name': 'sse', 'url': 'questions/tag/sse'},
            {'name': 'real-time', 'url': 'questions/tag/real-time'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 15,
                'text': 'Use SSE for server-to-client push notifications. Use WebSockets when you need bidirectional communication. SSE is simpler and works over HTTP.',
                'is_correct': True,
                'author': 'Real-time Dev',
                'created_at': '2024-01-03 10:45:00'
            }
        ]
    },
    {
        'id': 14,
        'profile_picture': 'profile-picture.png',
        'votes': 12,
        'title': 'TypeScript interface vs type alias',
        'url': 'questions/14',
        'description': 'What is the difference between interface and type in TypeScript? When should I use one over the other?',
        'answers_count': 8,
        'tags': [
            {'name': 'typescript', 'url': 'questions/tag/typescript'},
            {'name': 'javascript', 'url': 'questions/tag/javascript'},
            {'name': 'web-development', 'url': 'questions/tag/web-development'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 19,
                'text': 'Use interfaces for object shapes that can be extended. Use type aliases for unions, tuples, or more complex types. Interfaces are generally preferred for public APIs.',
                'is_correct': True,
                'author': 'TypeScript Guru',
                'created_at': '2024-01-02 08:30:00'
            }
        ]
    },
    {
        'id': 15,
        'profile_picture': 'profile-picture.png',
        'votes': 7,
        'title': 'Kubernetes pod scheduling issues',
        'url': 'questions/15',
        'description': 'My Kubernetes pods are stuck in Pending state. How can I debug scheduling issues and resource constraints?',
        'answers_count': 5,
        'tags': [
            {'name': 'kubernetes', 'url': 'questions/tag/kubernetes'},
            {'name': 'devops', 'url': 'questions/tag/devops'},
            {'name': 'containers', 'url': 'questions/tag/containers'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 13,
                'text': 'Check kubectl describe pod for events. Common issues: insufficient CPU/memory, node selector mismatches, taints/tolerations, or persistent volume claims.',
                'is_correct': True,
                'author': 'K8s Admin',
                'created_at': '2024-01-01 16:15:00'
            }
        ]
    },
    {
        'id': 16,
        'profile_picture': 'profile-picture.png',
        'votes': 10,
        'title': 'GraphQL vs REST API design',
        'url': 'questions/16',
        'description': 'When is GraphQL a better choice than REST for API design? What are the performance implications and complexity trade-offs?',
        'answers_count': 7,
        'tags': [
            {'name': 'graphql', 'url': 'questions/tag/graphql'},
            {'name': 'api', 'url': 'questions/tag/api'},
            {'name': 'rest', 'url': 'questions/tag/rest'}
        ],
        'answers': [
            {
                'id': 1,
                'profile_picture': 'profile-picture.png',
                'votes': 17,
                'text': 'GraphQL is great when clients need flexible data fetching. REST is simpler for CRUD operations. GraphQL can reduce over-fetching but adds complexity on the server.',
                'is_correct': True,
                'author': 'API Architect',
                'created_at': '2023-12-31 14:00:00'
            }
        ]
    }
]

def paginate(objects_list, request, per_page=10):

    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    
    return page

def index(request, *args, **kwargs):
    tag_name = request.GET.get('tag')
    
    questions_with_count = []
    for q in QUESTIONS:
        q_copy = q.copy()
        q_copy['answers_count'] = len(q.get('answers', []))
        questions_with_count.append(q_copy)
    
    if tag_name:
        filtered_questions = [
            q for q in questions_with_count 
            if any(tag['name'].lower() == tag_name.lower() for tag in q['tags'])
        ]
    else:
        filtered_questions = questions_with_count
    
    page = paginate(filtered_questions, request, per_page=4)
    
    return render(request, 'questions/index.html', {
        "questions": page,
        "popular_tags": POPULAR_TAGS,
        "best_members": BEST_MEMBERS,
        "tag_name": tag_name,
        "page_title": "New Questions"
    })

def tag_view(request, tag_name=None):
    tag_name = request.GET.get('tag', tag_name)
    
    if tag_name:
        filtered_questions = [
            q for q in QUESTIONS 
            if any(tag['name'].lower() == tag_name.lower() for tag in q['tags'])
        ]
    else:
        filtered_questions = QUESTIONS
    
    page = paginate(filtered_questions, request, per_page=5)
    
    return render(request, 'questions/tag.html', {
        'questions': page,
        'tag_name': tag_name,
        'popular_tags': POPULAR_TAGS,  
        'best_members': BEST_MEMBERS   
    })

def question_detail(request, question_id):
    question = None
    for q in QUESTIONS:
        if q['id'] == int(question_id):
            question = q
            question['answers_count'] = len(question.get('answers', []))
            break
    
    if not question:
        from django.http import Http404
        raise Http404("Question not found")
    
    return render(request, 'questions/question.html', {
        'question': question,
        'popular_tags': POPULAR_TAGS, 
        'best_members': BEST_MEMBERS   
    })

def ask_view(request, *args, **kwargs):
    return render(request, 'questions/ask.html', {
        'popular_tags': POPULAR_TAGS,
        'best_members': BEST_MEMBERS
    })

def hot_questions(request):
    
    sorted_questions = sorted(QUESTIONS, key=lambda x: x['votes'], reverse=True)
    
    page = paginate(sorted_questions, request, per_page=4)
    
    return render(request, 'questions/hot.html', {
        "questions": page,
        "popular_tags": POPULAR_TAGS,
        "best_members": BEST_MEMBERS,
        "page_title": "Hot Questions"
    })


def _get_question(q_id: int) -> dict:
    for q in QUESTIONS:
        if q.get('id') == q_id:
            return q
    raise Http404("Question not found")

def _get_answer(question: dict, a_id: int) -> dict:
    for a in question.get('answers', []):
        if a.get('id') == a_id:
            return a
    raise Http404("Answer not found")

def _redirect_back_or_detail(request, question: dict):
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    try:
        return redirect(reverse("questions:detail", args=[question['id']]))
    except Exception:
        return redirect(f"/{question.get('url','')}")

@require_POST
def mark_answer_correct(request, question_id: int, answer_id: int):
    question = _get_question(question_id)
    _get_answer(question, answer_id) 

    for ans in question.get('answers', []):
        ans['is_correct'] = (ans.get('id') == answer_id)

    return _redirect_back_or_detail(request, question)

@require_POST
def unmark_answer_correct(request, question_id: int, answer_id: int):
    question = _get_question(question_id)
    answer = _get_answer(question, answer_id)
    answer['is_correct'] = False
    return _redirect_back_or_detail(request, question)
