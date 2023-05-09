from django.shortcuts import render
from PokerModel.PokerModel.Game import Game

# # Create your views here.

game = Game()

def index(request):
    if request.method == 'GET':
        game.reset()
        return render(request, 'PokerWebApp/index.html', context=game.create_context())
    else:
        player_action(request)
        if game.done:
            return render(request, 'PokerWebApp/winnerPage.html', {"winner": game.get_absolute_winner()})
        else:
            return render(request, 'PokerWebApp/index.html', context=game.create_context())


def player_action(request):
    if request.method == 'POST':
        if 'show_cards' == request.POST['action']:
            game.flip_show_cards()
        elif 'Fold' == request.POST['action']:
            game.step(0)
        elif 'Check' == request.POST['action']:
            game.step(1)
        elif 'Call' == request.POST['action']:
            game.step(2)
        elif 'Min_Raise' == request.POST['action']:
            game.step(3)
        elif 'Big_Raise' in request.POST['action']:
            game.step(4)
        else:
            game.step(0)

