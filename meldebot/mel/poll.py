###############################################################################
# Project: Mort de Gana Bot
# Authors:
# - Ytturi
# - gdalmau
# Descr: Polling manager
# Commands:
# - Poll: Send a poll with a specified message. Usage: `/poll {message}`
###############################################################################
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from random import choice, randint
import logging

# Self imports
from meldebot.mel.gif import get_gifs
from meldebot.mel.utils import send_typing_action, get_username

# Mort de Gana POLL MANAGER

# POLL KEYBOARD
POLL_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('MEL', callback_data='vote MEL'),
        InlineKeyboardButton('MEL + 1', callback_data="vote MEL+1"),
        InlineKeyboardButton('MEL - 1', callback_data="vote MEL-1"),
    ],
    [
        InlineKeyboardButton('MOTO', callback_data='vote MOTO'),
    ],
])

# POLL START


def get_question(extra_text):
    question = "Mel o no?\n"
    if extra_text:
        question = '{}\n{}'.format(extra_text, question)
    return question


def get_answers(status=None):
    if status is None:
        status = ['', '']
    answer = 'MEL!\n{}- {}\nMOTO!\n{}- {}'.format(
        recount_result(status[0]),status[0],
        recount_result(status[1]),status[1],
    )
    return answer

def get_moto_quote() -> str:
    """Generate a random text for motos

    Returns:
        str: Moto quote
    """
    moto_quote_set = [
        f'Vaig al gym, la idea es anarhi {randint(1,20)} cops per setmana',
        f'Tinc hora a la pelu que nomes hi vaig {randint(1,20)} cops per setmana',
        f'Fa {randint(2,30)} anys plovia',
        'Soc un mort de gana',
        'Plou i fa sol, em quedo a casa sol',
        "Jo vindria, pero m'agrada fer motos",
    ]

    return choice(moto_quote_set)

@send_typing_action
def start_poll(update, context):
    # TODO: Remove querying message
    text = '{}\n{}'.format(
        get_question(extra_text=' '.join(context.args)),
        get_answers()
    )
    message = update.message.reply_text(
        text,
        reply_markup=POLL_KEYBOARD,
    )


POLL_START_HANDLER = CommandHandler('poll', start_poll, pass_args=True)


# POLL VOTE HANDLER

def result_user_votes(result):
    break_idx = False
    for idx, char in enumerate(result):
        if char == '-':
            break_idx = idx
            break
        if char == '@':
            # If there is no result part and we reach a username
            break
    if break_idx is False and result:
        return result.split(',')
    break_idx += 1
    votes = result[break_idx:].strip()
    if votes:
        return votes.split(',')
    else:
        return []


def recount_result(result):
    """Parse the result line and count the votes"""
    user_votes = result_user_votes(result)
    total = 0
    for vote in user_votes:
        if not vote:
            break
        total += 1
        if '+' in vote:
            total += int(vote[vote.index('+')+1:])
    return total


def insert_user_in_result(results, result_idx, user, extra=False):
    """
    Parse the result line and add the user and any extras.
      If the user is present in the other results string, remove it.
    """
    def search_user_vote(arr, user):
        user_vote_idx = False
        for idx, vote in enumerate(arr):
            if user in vote:
                user_vote_idx = idx
        return user_vote_idx

    def get_user_extra_vote(arr, user):
        idx = search_user_vote(arr, user)   # Search vote
        if idx is False:
            return 0
        vote = arr[idx][len(user)+2:]       # Remove username from vote
        vote.strip()
        return int(vote) if vote else 0     # If any vote, parse to int

    # Init vote text
    text = '@{}'.format(user)
    # Update results
    votes = result_user_votes(results[result_idx])
    # Find last vote (if any)
    user_vote_idx = search_user_vote(votes, user)
    if user_vote_idx is not False:
        # IF exists
        if extra:
            # If extra, update it
            extra = extra + get_user_extra_vote(votes, user)
            if extra and extra > 0: # Can't set lower than 0
                text += '+{}'.format(extra)
        votes[user_vote_idx] = text
        results[result_idx] = ','.join(votes) # UPDATE
    else:
        # IF not exists, ADD the new vote
        # IF extra, add it
        if extra and extra > 0: # Can't set lower than 0
            text += '+{}'.format(extra)
        votes.append(text)
        votes = sorted(votes)                   # SORT
        results[result_idx] = ','.join(votes) # UPDATE
    # Clean other results and DEL old vote (if any)
    other_idx = 0 if result_idx else 1
    votes = result_user_votes(results[other_idx])
    user_vote_idx = search_user_vote(votes, user)
    if user_vote_idx is not False:
        del votes[user_vote_idx]
    results[other_idx] = ','.join(votes) # UPDATE
    return results


def update_poll_message(text, user, query):
    question = text.split('\n')[:-4] 
    results = text.split('\n')[-3:]
    results = [results[0], results[-1]]
    # DATA="vote [MEL|MOTO|MEL+1|MEL-1]"
    vote = query.data[5:]
    if "MEL" in vote:
        extra = int(vote[3:]) if vote[3:] else 0
        results = insert_user_in_result(
            results, 0, user=user, extra=extra
        )
    else:
        results = insert_user_in_result(results, 1, user=user)

    question.append(get_answers(results))
    return '\n'.join(question)

def vote_poll(update, context):
    username = get_username(update.effective_user)
    message_text = update_poll_message(
        text=update.effective_message.text,
        user=username,
        query=update.callback_query
    )
    if message_text == update.effective_message.text:
        return
    update.effective_message.edit_text(
        text=message_text,
        reply_markup=POLL_KEYBOARD
    )
    if 'MOTO' in update.callback_query.data:
        update.effective_message.reply_animation(
            get_gifs('moto'), caption=f'{username}: {get_moto_quote()}', quote=True)


POLL_VOTE_HANDLER = CallbackQueryHandler(vote_poll, pattern=r'^vote')


# HANDLERS to register


POLL_HANDLERS = [
    POLL_START_HANDLER,
    POLL_VOTE_HANDLER,
]