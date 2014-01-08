from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404

from pingpong.dashboard.forms import UpcomingMatchesFromset, CurrentMatchesFromset, SetScoreForm
from pingpong.models import Category, Match, Table


def dashboard(request):
    group_matches = Match.ready_group_matches()
    bracket_matches = Match.ready_bracket_matches()
    doubles_matches = Match.ready_doubles_matches()

    if request.method == 'POST':
        formset = UpcomingMatchesFromset(request.POST)
        if formset.is_valid():
            instances = formset.save()
            matches_to_print = [instance for instance in instances
                                if instance is not None and instance.group is None]

            if matches_to_print:
                from pingpong.printing.helpers import print_matches
                print_matches(matches_to_print)
            return redirect('upcoming_matches')
    else:
        formset = UpcomingMatchesFromset(queryset=bracket_matches | group_matches | doubles_matches)

    return render(request, 'pingpong/dashboard/dashboard.html', {
        'formset': formset,
        'group_matches': group_matches,
        'bracket_matches': bracket_matches,
        'doubles_matches': doubles_matches,
    })


def set_score(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    matches = table.current_matches()

    if request.method == 'POST':
        set_score_form = SetScoreForm(request.POST, instance=matches.get())
        if set_score_form.is_valid():
            set_score_form.save()
            return redirect(reverse('upcoming_matches'))

    if request.is_ajax():
        template = 'pingpong/snippets/set_score_form.html'
    else:
        template = 'pingpong/dashboard/set_score.html'
    return render(request, template, dict(
        table=table,
        matches=matches,
    ))
