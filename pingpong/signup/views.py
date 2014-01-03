from django.core.urlresolvers import reverse
from django.db.models import Count
from django.db.models.deletion import Collector
from django.shortcuts import render, get_object_or_404, redirect

from pingpong.bracket.helpers import create_pair_brackets
from pingpong.bracket.models import Bracket
from pingpong.group.forms import NumberOfGroupsForm, SelectLeadersFormSet
from pingpong.models import Category, Player, Double, Group, GroupMember
from pingpong.printing.helpers import print_groups
from pingpong.signup.forms import PlayerFormSet, CategoryEditForm, CategoryAddForm, DoubleFormSet


def index(request):
    try:
        category = Category.objects.all()[0]
        return redirect(reverse('category_edit', kwargs=dict(category_id=category.id)))
    except IndexError:
        pass

    return redirect(reverse('category_add'))


def category_details(request, category_id):
    category = get_object_or_404(Category.objects.annotate(Count('bracket'), Count('group')),
                                 id=category_id)

    return render(request, 'pingpong/category.html', dict(category=category))


def edit_category(request, category_id):
    category = get_object_or_404(Category.objects.annotate(Count('bracket'), Count('group')),
                                 id=category_id)

    if request.method == 'POST':
        category_fields = CategoryEditForm(request.POST, instance=category, prefix='category_fields')

        if category_fields.is_valid():
            category_fields.save()

            return redirect(reverse("category", kwargs=dict(category_id=category.id)))
    else:
        category_fields = CategoryEditForm(instance=category, prefix='category_fields')

    if request.is_ajax():
        template = 'pingpong/snippets/edit_category_form.html'
    else:
        template = 'pingpong/category_edit.html'
    return render(request, template,
                  dict(category=category,
                       category_fields_form=category_fields))


def edit_category_players(request, category_id):
    category = get_object_or_404(Category.objects.annotate(Count('bracket'), Count('group')),
                                 id=category_id)

    if request.method == 'POST':
        players = players_formset(category, request.POST)

        if players.is_valid():
            players.save()
            return redirect(reverse("category", kwargs=dict(category_id=category.id)))
    else:
        players = players_formset(category)

    if request.is_ajax():
        template = 'pingpong/snippets/edit_players_form.html'
    else:
        template = 'pingpong/category_edit_players.html'
    return render(request, template,
                  dict(category=category,
                       players_formset=players))


def players_formset(category, post_data=None):
    if category.type == Category.SINGLE:
        return _players_formset(category, post_data, Player, PlayerFormSet)
    else:
        return _players_formset(category, post_data, Double, DoubleFormSet)


def _players_formset(category, post_data, Model, Formset):
    queryset = Model.objects.order_by('id').filter(category=category)
    formset = Formset(post_data, queryset=queryset, prefix='players')
    formset.category = category
    return formset


def add_category(request):
    if request.method == 'POST':
        form = CategoryAddForm(request.POST)
        if form.is_valid():
            category = form.save()
            return redirect(reverse('category_edit', kwargs=dict(category_id=category.id)))
    else:
        form = CategoryAddForm()

    categories = Category.objects.annotate(player_count=Count('players'))
    return render(request, 'pingpong/category_add.html',
                  dict(form=form,
                       categories=categories))


def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        if 'yes' in request.POST:
            category.delete()
            return redirect(reverse('signup'))
        else:
            return redirect(reverse('category_edit', kwargs=dict(category_id=category.id)))

    return render(request, 'pingpong/confirm_deletion.html', dict(
        object_type=category._meta.verbose_name,
        object_description=u'%s (%s)' % (category.description, category.name),
        related_objects=get_related_objects([category]),
    ))


def delete_groups(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    groups = category.group_set.all()

    if request.method == 'POST':
        if 'yes' in request.POST:
            groups.delete()
        return redirect(reverse('category_edit', kwargs=dict(category_id=category.id)))

    return render(request, 'pingpong/confirm_deletion.html', dict(
        object_type=Group._meta.verbose_name_plural,
        object_description=groups,
        related_objects=get_related_objects(groups),
    ))


def delete_brackets(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    brackets = category.bracket_set.all()

    if request.method == 'POST':
        if 'yes' in request.POST:
            brackets.delete()
        return redirect(reverse('category_edit', kwargs=dict(category_id=category.id)))

    return render(request, 'pingpong/confirm_deletion.html', dict(
        object_type=Bracket._meta.verbose_name_plural,
        object_description=brackets,
        related_objects=get_related_objects(brackets),
    ))


def get_related_objects(obj):
    collector = Collector(using='default')
    collector.collect(obj)
    return [(model._meta.verbose_name_plural, instance) for model, instance in collector.instances_with_model()]


def create_groups(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        number_of_groups = NumberOfGroupsForm(request.POST)
        group_leaders = SelectLeadersFormSet(request.POST)
        group_leaders.category = category

        if number_of_groups.is_valid() and group_leaders.is_valid():
            group_leaders.create_groups(category, number_of_groups.as_int())
            print_groups(category)

            return redirect(reverse('category', kwargs=dict(category_id=category.id)))
    else:
        number_of_groups = NumberOfGroupsForm()
        group_leaders = SelectLeadersFormSet(queryset=category.players.order_by('id'))

    return render(request, 'pingpong/create_groups.html',
                  dict(category=category,
                       formset=group_leaders,
                       numgroups=number_of_groups))
