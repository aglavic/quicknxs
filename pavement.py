from paver.tasks import task, BuildFailure, needs
from paver.easy import sh

''' paver allows to define a global built '''

@task
def unit_tests():
    sh('nosetests --rednose --with-coverage -v tests/unit')
    
@task
def acceptance_tests():
    sh('lettuce tests/bdd')
    
@needs('unit_tests','acceptance_tests')
@task
def default():
    pass