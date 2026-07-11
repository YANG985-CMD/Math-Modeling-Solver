function result = topsis(data, weights, benefitMask)
%TOPSIS Rank alternatives with TOPSIS.
if nargin < 2 || isempty(weights)
    weights = ones(1, size(data, 2));
end
if nargin < 3 || isempty(benefitMask)
    benefitMask = true(1, size(data, 2));
end
weights = weights ./ sum(weights);
normData = data ./ sqrt(sum(data .^ 2, 1));
weighted = normData .* weights;
idealBest = zeros(1, size(data, 2));
idealWorst = zeros(1, size(data, 2));
for j = 1:size(data, 2)
    if benefitMask(j)
        idealBest(j) = max(weighted(:, j));
        idealWorst(j) = min(weighted(:, j));
    else
        idealBest(j) = min(weighted(:, j));
        idealWorst(j) = max(weighted(:, j));
    end
end
distBest = sqrt(sum((weighted - idealBest) .^ 2, 2));
distWorst = sqrt(sum((weighted - idealWorst) .^ 2, 2));
scores = distWorst ./ (distBest + distWorst);
[~, ranking] = sort(scores, "descend");
result.scores = scores;
result.ranking = ranking;
result.idealBest = idealBest;
result.idealWorst = idealWorst;
end
