from django import template
from django.db.models import Count
from django.template import TemplateSyntaxError, NodeList, Context, Variable
from django.template.loader import render_to_string

from pingpong.bracket.models import Bracket
from pingpong.models import Category, GroupMember, Table
from pingpong.signup.forms import CategoryEditForm
from pingpong.signup.views import players_formset


register = template.Library()


@register.inclusion_tag('pingpong/snippets/category_list.html')
def list_categories(category):
    categories = Category.objects.filter(type=category.type).annotate(player_count=Count('players'))
    return {
        'categories': categories
    }


@register.inclusion_tag('pingpong/snippets/edit_category_form.html', takes_context=True)
def edit_category(context, category):
    if 'category_fields_form' in context:
        category_fields = context['category_fields_form']
    else:
        category_fields = CategoryEditForm(instance=category, prefix='category_fields')

    return {
        'modal': False,
        'category': category,
        'category_fields_form': category_fields,
    }


@register.inclusion_tag('pingpong/snippets/edit_players_form.html', takes_context=True)
def edit_category_players(context, category):
    if 'players_formset' in context:
        players = context['players_formset']
    else:
        players = players_formset(category)

    return {
        'modal': False,
        'category': category,
        'players_formset': players,
    }


@register.inclusion_tag('pingpong/snippets/groups.html')
def show_groups(category):
    members = GroupMember.for_category(category)

    class AnonymousUser:
        @staticmethod
        def is_authenticated():
            return False

    return {
        'group_members': members,
        'user': AnonymousUser,
    }


@register.inclusion_tag('pingpong/snippets/brackets.html')
def show_brackets(category):
    brackets = Bracket.objects.filter(category=category)

    return {
        'brackets': brackets,
    }


@register.tag
def panel(parser, token):
    bits = list(token.split_contents())
    if len(bits) == 1:
        bits.append('True')
    if len(bits) == 2:
        modal = parser.compile_filter(bits[1])
    else:
        raise TemplateSyntaxError("%r takes at most one argument" % bits[0])

    title = parser.parse(('body', 'footer', 'endpanel',))
    body = footer = NodeList()
    token = parser.next_token()
    if token.contents == 'body':
        body = parser.parse(('footer', 'endpanel',))
        token = parser.next_token()
    if token.contents == 'footer':
        footer = parser.parse(('endpanel',))
    parser.delete_first_token()
    return PanelNode(title, body, footer, modal)


class PanelNode(template.Node):
    def __init__(self, title, body, footer, modal):
        self.title = title
        self.body = body
        self.footer = footer
        self.modal = modal

    def render(self, context):
        modal = self.modal.resolve(context, True)
        if modal is None:
            modal = True
        if modal:
            template = 'pingpong/dialogs/modal.html'
        else:
            template = 'pingpong/dialogs/panel.html'

        return render_to_string(template, Context(dict(
            title=self.title.render(context),
            body=self.body.render(context),
            footer=self.footer.render(context),
        )))

@register.inclusion_tag('pingpong/snippets/tables.html')
def show_tables():
    tables = Table.objects.order_by('display_order').prefetch_related('bracketslot_set', 'group_set', 'group_set__category')
    return {
        'tables': tables,
    }


@register.inclusion_tag('pingpong/snippets/table.html')
def show_table(table):
    return {
        'table': table,
    }
