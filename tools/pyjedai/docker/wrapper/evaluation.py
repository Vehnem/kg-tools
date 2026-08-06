def evaluate(predicted, gt):
    predicted = set(predicted)
    gt = set(gt.itertuples(index=False, name=None))

    tp = len(predicted & gt)
    fp = len(predicted - gt)
    fn = len(gt - predicted)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

    return {"TP": tp, "FP": fp, "FN": fn, "Precision": precision, "Recall": recall, "F1": f1}