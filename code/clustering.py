from code.utils import calculate_distances, fix_cluster_labels

from sklearn.cluster import AgglomerativeClustering, DBSCAN
from sklearn import metrics
import pandas as pd
from tqdm import tqdm

########################################################################################################################################################################################################

# cluster and select the best clustering for the provided data, using agglomerative clustering
def create_cluster_agglo (data, penalty):
  stdev = 0.127
  sd_threshold = stdev

  max_dist, min_dist, avg_dist, median_dist = calculate_distances(data)

  # determine distance thresholds
  base = median_dist
  dist_range = max_dist - median_dist
  step = dist_range/7
  distances = []
  for i in range(5):
    base += step
    distances.append(base)
  #print(median_dist, max_dist)
  #print(distances)
  
  # variables to keep track of best clustering
  best_score = -2
  best_clustering = None
  best_dist = None
  best_linkage = None
  best_num_clusters = 0

  linkage_types = ['complete', 'average', 'single',]

  total_progress = 15
  progress_bar = tqdm(total=total_progress)
  # try each distance with each linkage type
  for i, dist_thres in enumerate(distances):
    for linkage in linkage_types:
      progress_bar.update(1)
      # perform the clustering
      clustering = AgglomerativeClustering(n_clusters=None, linkage=linkage, distance_threshold=dist_thres)
      labels = clustering.fit_predict(data)
      num_clusters = len(set(labels))
      #print("Clustering with linkage", linkage, "and distance", i, round(dist_thres, 4), "created", num_clusters, "clusters.")

      if len(set(labels)) > 1:
        # calculate score and apply penalty
        score = metrics.silhouette_score(data, labels)
        if penalty and len(set(labels)) == 2:
          score = score * 0.85
        # better score and more clusters OR significantly better score and less clusters OR current best has a lot of clusters
        if  ((score > best_score and num_clusters > best_num_clusters) or
            (score > best_score + sd_threshold and num_clusters < best_num_clusters) or
            (best_num_clusters > 10 and score > best_score)):
          ##print("New best: score:", round(score, 4), "|  # clusters:", num_clusters)
          best_score = score
          best_clustering = labels
          best_num_clusters = num_clusters
          best_dist = i
          best_linkage = linkage
          print("New pb")

  progress_bar.close()

  if best_score == -2:
    return None
  else:
    print("Final best score of", round(best_score, 3), "found for distance", best_dist, "of", round(distances[best_dist], 4), "with linkage type", best_linkage)
    print("Number of new clusters:", len(list(set(best_clustering))))
    return best_clustering

########################################################################################################################################################################################################

# cluster and select the best clustering for the provided data, using DBSCAN clustering
def create_cluster_dbscan (data):
  stdev = 0.127
  sd_threshold = stdev

  max_dist, min_dist, avg_dist, median_dist = calculate_distances(data)

  # determine initial distance thresholds
  distances = []

  steps = 15
  step = (max_dist - min_dist) / steps

  next_dist = min_dist + step
  for i in range(5):
    distances.append(next_dist)
    next_dist += step

  best_score = -2
  best_dist = 0
  best_num_clusters = 0
  best_clustering = None

  # create progress bar
  total_progress = 5
  progress_bar = tqdm(total=total_progress)

  # try each distance
  for dist in distances:
    progress_bar.update(1)
    #perform the clustering
    dbscan = DBSCAN(eps=dist, min_samples=1).fit(data)
    num_clusters = len(set(dbscan.labels_))

    if num_clusters > 1:
      # calculate the score
      score = metrics.silhouette_score(data, dbscan.labels_)

      # better score and more clusters OR significantly better score and less clusters OR current best has a lot of clusters
      if ((score > best_score and num_clusters > best_num_clusters) or
       (score > (best_score + sd_threshold) and num_clusters < best_num_clusters) or
       (best_num_clusters > 10 and score > best_score)):
        ##print("New best: score:", round(score, 4), "|  # clusters:", num_clusters)
        best_score = score
        best_num_clusters = num_clusters
        best_clustering = dbscan
        best_dist = dist

  progress_bar.close()

  if best_score == -2:
    print("Every attempt created only one cluster. Trying with agglomerative clustering")
    labels = create_cluster_agglo(data, False)

    return labels

  print("Best score of", round(best_score, 3), "found for esp =", round(best_dist, 4))
  print("Number of new clusters:", len(list(set(best_clustering.labels_))))
  return best_clustering.labels_

########################################################################################################################################################################################################

# start the initial clustering 
def start_initial_clustering (dataset, algorithm, penalty):
  # prepare data
  X = dataset['location-long'].values.tolist()
  Y = dataset['location-lat'].values.tolist()

  xy_data = list(zip(X,Y))

  # agglomerative clustering
  if algorithm == 'agglo':
    labels = create_cluster_agglo(xy_data, penalty)
  # DBSCAN clustering
  elif algorithm == 'dbscan':
    labels = create_cluster_dbscan (xy_data)

  if labels is not None:
    # add labels to the data
    dataset['label'] = labels

    return dataset
  
  print("Every attempt created only one cluster. No best clustering formation found. Please inspect your data.")
  return None

########################################################################################################################################################################################################

# make an adjustment: recluster the given clusters
def adjust_reclustering(dataset, algorithm, clusters, penalty):
  # select data with these clusters
  data_recluster = dataset[dataset['label'].isin(clusters)].copy()
  data_original = dataset[~dataset['label'].isin(clusters)].copy()

  # prepare data
  X = data_recluster['location-long'].values.tolist()
  Y = data_recluster['location-lat'].values.tolist()

  xy_data = list(zip(X,Y))

  # agglomerative clustering
  if algorithm == 'agglo':
    labels = create_cluster_agglo(xy_data, penalty)
  # DBSCAN clustering
  elif algorithm == 'dbscan':
    labels = create_cluster_dbscan (xy_data)

  # succesful clustering
  if labels is not None:
    # merge data with labels
    new_label_indexes = fix_cluster_labels(list(set(data_original['label'].tolist())), list(set(labels)))
    reclustered_labels = [new_label_indexes[label] for label in labels]
    data_recluster['label'] = reclustered_labels

    # combine initial and new clustering
    data_new = pd.concat([data_recluster, data_original]).sort_values(by=['timestamp']).reset_index(drop=True)

    return data_new
  else:
    print("Only 1 cluster created - clustering cancelled.")
    return None

########################################################################################################################################################################################################

# make an adjustment: merge the given clusters into one cluster
def adjust_merge(dataset, clusters):
  # select and merge data
  new_cluster = min(clusters)
  data_to_merge = dataset[dataset['label'].isin(clusters)].copy()
  data_to_merge['label'] = new_cluster

  # find new labels
  original_data = dataset[~dataset['label'].isin(clusters)].copy()
  new_total_clusters = len(original_data['label'].unique().tolist()) + 1
  original_data_labels = original_data['label'].unique().tolist()

  new_label_indexes = {}
  for i in range(new_total_clusters):
    if i == new_cluster:
      continue
    # update dictionary; for this old label, have this new value
    new_label_indexes[original_data_labels[0]] = i
    original_data_labels.pop(0)
    # make sure we exit when we're done
    if len(original_data_labels) == 0:
      break

  # set new labels
  old_labels = original_data['label'].values.tolist()
  new_labels = [new_label_indexes[label] for label in old_labels]
  original_data['label'] = new_labels

  # merge new and original data
  data_new = pd.concat([data_to_merge, original_data]).sort_values(by=['timestamp']).reset_index(drop=True)

  return data_new