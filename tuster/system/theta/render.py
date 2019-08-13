from jinja2 import Environment, PackageLoader

def render(**kwargs):
    env = Environment(loader=PackageLoader('tuster', 'system/theta'))

    template = env.get_template('template.sh')

    rendering = template.render(**kwargs)

    return rendering