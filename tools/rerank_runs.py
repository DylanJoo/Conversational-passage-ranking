from tqdm import tqdm
import collections
import argparse
from utils import load_runs

def append_scores(path_run, path_score):
    """
    path_run: the baseline run
    path_score: the text file of scores of each query-passage pair.
    """
    # load runing file
    run_dict = collections.defaultdict(list)
    with open(path_run, 'r') as frun, open(path_score, 'r') as fscore:
        for line_run, line_score in tqdm(zip(frun, fscore)):
            # [TODO] Maybe hybrid ranking here.
            qid, _, docid, rank, score, _ = line_run.strip().split()
            # use the new score
            score = line_score.strip()

            if int(rank) <= args.topk:
                if args.rrf:
                    run_dict[qid] += [(docid, float(score), 1/(60+int(rank)))]
                else:
                    run_dict[qid] += [(docid, float(score))]

    return run_dict


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=str)
    parser.add_argument("--scores", type=str, default='the text files with scores.')
    parser.add_argument("--reranked",type=str)
    parser.add_argument("--topk", type=int)
    parser.add_argument("--prefix",type=str, default='monot5')
    parser.add_argument("--rrf", default=False, action='store_true')
    args = parser.parse_args()

    run_with_probs = append_scores(args.baseline, args.scores)

    with open(args.reranked, 'w') as f:
        for qid, candidates in tqdm(run_with_probs.items()):
            # Using true prob as score, so reverse the order.
            sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)

            # ranked list fusion 
            if args.rrf:
                for idx, (pid, t_prob, rr_retrieval) in enumerate(sorted_candidates):
                    t_rrf = 1/(60+int(idx+1)) + rr_retrieval
                    sorted_candidates[idx]  = (pid, t_rrf) 
                sorted_candidates = sorted(sorted_candidates, key=lambda x: x[1], reverse=True)

            for idx, (pid, t_prob) in enumerate(sorted_candidates):
                example = f'{qid} Q0 {pid} {str(idx+1)} {t_prob} {args.prefix}\n'
                f.write(example)
