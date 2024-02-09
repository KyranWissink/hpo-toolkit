import argparse
import logging
import sys
import datetime
import timeit
import typing
from collections import defaultdict

import pandas as pd

import hpotk

hpotk.util.setup_logging()
logger = logging.getLogger(__name__)

COLUMNS = ('group', 'method', 'payload', 'throughput')

# We'll bench traversals using these terms:
CURIE2LABEL = {
    'HP:0000118': 'Phenotypic abnormality',  # almost at the top of all terms
    'HP:0001454': 'Abnormality of the upper arm',
    'HP:0001166': 'Arachnodactyly',  # 2 parents
    'HP:0001250': 'Seizure',
    'HP:0009439': 'Short middle phalanx of the 3rd finger',  # 3 parents
}


def bench_func_throughput(func: typing.Callable[[], typing.Any],
                          number: int) -> float:
    # `timeit` returns the time it takes to execute the main statement a number of times,
    # measured in seconds as a float.
    cum_exec_time = timeit.timeit(func, number=number)
    return number / cum_exec_time


def bench_base_graph(fpath_hpo: str,
                     number: int = 1000) -> typing.Mapping[str, typing.Sequence]:
    factory = hpotk.graph.IncrementalCsrGraphFactory()
    ontology = hpotk.load_minimal_ontology(fpath_hpo, graph_factory=factory)
    graph = ontology.graph

    results = defaultdict(list)

    for curie, label in CURIE2LABEL.items():
        term_id = hpotk.TermId.from_curie(curie)
        label = ontology.get_term_name(curie)
        payload = f'{label} [{curie}]'
        logger.info('Timing %s', payload)

        benches = {
            'get_parents': lambda: list(graph.get_parents(term_id)),
            'get_ancestors': lambda: list(graph.get_ancestors(term_id)),
            'get_children': lambda: list(graph.get_children(term_id)),
            'get_descendants': lambda: list(graph.get_descendants(term_id)),
        }

        for method in benches:
            bench = benches[method]
            logger.info(f' - {method}')
            throughput = bench_func_throughput(bench, number)
            results['method'].append(method)
            results['payload'].append(payload)
            results['throughput'].append(throughput)

    return results


def bench_indexed_graph(fpath_hpo: str,
                        number: int = 1000) -> typing.Mapping[str, typing.Mapping[str, float]]:
    factory = hpotk.graph.CsrIndexedGraphFactory()
    ontology = hpotk.load_minimal_ontology(fpath_hpo, graph_factory=factory)
    graph: hpotk.graph.IndexedOntologyGraph = ontology.graph

    results = defaultdict(list)
    for curie, label in CURIE2LABEL.items():
        term_id = hpotk.TermId.from_curie(curie)
        idx = graph.node_to_idx(term_id)
        label = ontology.get_term_name(curie)
        payload = f'{label} [{curie}]'
        logger.info('Timing %s', payload)
        benches = {
            'get_parents_idx': lambda: list(graph.get_parents_idx(idx)),
            'get_parents': lambda: list(graph.get_parents(term_id)),
            'get_ancestor_idx': lambda: list(graph.get_ancestor_idx(idx)),
            'get_ancestors': lambda: list(graph.get_ancestors(term_id)),
            'get_children_idx': lambda: list(graph.get_children_idx(idx)),
            'get_children': lambda: list(graph.get_children(term_id)),
            'get_descendant_idx': lambda: list(graph.get_descendant_idx(idx)),
            'get_descendants': lambda: list(graph.get_descendants(term_id)),
        }

        for method in benches:
            bench = benches[method]
            logger.info(f' - {method}')
            throughput = bench_func_throughput(bench, number)
            results['method'].append(method)
            results['payload'].append(payload)
            results['throughput'].append(throughput)

    return results


def bench(fpath_hpo: str, number: int, revision: str):
    logger.info(f'Iterating {number:,d} times')

    bench_groups = {
        'IndexedOntologyGraph': bench_indexed_graph,
        'OntologyGraph': bench_base_graph,
    }

    results = []
    for group in bench_groups:
        logger.info(f'Benching `{group}`')
        bench_func = bench_groups[group]
        data = bench_func(fpath_hpo, number=number)

        result = pd.DataFrame(data)
        result['group'] = group
        results.append(result)


    df = pd.concat(results)
    df['revision'] = revision
    df = df.set_index(['revision', 'method', 'group', 'payload']).sort_index()

    fpath_df = f'graph_traversal-{number}-{revision}.csv'
    df.to_csv(fpath_df)


def main() -> int:
    """
    Benchmark graph traversals.
    """
    parser = argparse.ArgumentParser(prog='graph_traversal',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description=main.__doc__)
    parser.add_argument('--hpo', required=True, help='Path to HPO JSON file')
    parser.add_argument('-n', '--number', default=1_000, help='Number of iterations of each bench')
    parser.add_argument('-r', '--revision', default=None, help='The benchmark revision')

    argv = sys.argv[1:]
    if len(argv) == 0:
        parser.print_help()
        return 1

    args = parser.parse_args(argv)
    if args.revision is None:
        revision = datetime.datetime.now().strftime('%Y-%m-%d')
    else:
        revision = args.revision
    bench(args.hpo, args.number, revision)

    return 0


if __name__ == '__main__':
    sys.exit(main())
