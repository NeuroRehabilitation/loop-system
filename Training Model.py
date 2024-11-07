import warnings

from Signals_Processing import *

warnings.filterwarnings("ignore")

"""Load Data from Folder"""

folder = os.getcwd() + "\\Training Models\\"
participant = "P3"
path = folder + participant

data = {}
fs = 100
resolution = 16
sensors = ["ECG", "EDA", "RESP"]

try:
    if os.path.isdir(path):
        print(f"Loading data from {path}.")

        xdf_files = [file for file in os.listdir(path) if file.endswith('.xdf')]

        if not xdf_files:
            print("No .xdf files found.")
        else:
            for file in xdf_files:
                file_path = os.path.join(path, file)

                condition = file.split("_")[1].split(".")[0]

                data[condition] = Run_files(file_path)

except FileNotFoundError:
    print(f"The directory {path} does not exist.")
except Exception as e:
    print(f"An error occurred: {e}")

"""Signals Processing"""
signals = getSignals(data, "OpenSignals", "PsychoPy Markers", "PsychoPy Ratings", sensors=sensors)
epochs_markers, ratings = getEvents(signals)

"""Baseline Dataframe"""
baseline_signals = nk.epochs_create(
    pd.DataFrame.from_dict(signals["Baseline"]["Signals"]),
    events=epochs_markers["Baseline"]["Onset_index"],
    sampling_rate=fs,
    epochs_start=0,
    epochs_end=epochs_markers["Baseline"]["EventsDiff"],
)
df_baseline = getDataframe(baseline_signals["1"], fs, resolution)

try:
    df_baseline.to_csv(path + "\\df_baseline.csv", sep=";")
    print(f"Baseline Dataframe saved to {path}.")
except Exception as e:
    print(f"An error occurred saving the Baseline Dataframe: {e}")

"""Create epochs from signals"""
epochs_data = getSignalsEpochs(signals, epochs_markers, ratings, window=60, fs=fs)
print("Epochs Created Successfully.")

"""Extract features from Epochs"""
features = getFeatures(epochs_data, fs=fs, resolution=resolution)

"""Features Dataframe"""
dataframe = getSignalsDataframe(features, epochs_data)
dataframe.replace([np.inf, -np.inf], np.nan, inplace=True)

try:
    dataframe.to_csv(path + "\\dataframe.csv", sep=";")
    print(f"Features Dataframe saved to {path}.")
except Exception as e:
    print(f"An error occurred saving the Features Dataframe: {e}")

"""Subtract baseline features to dataframe"""
columns = dataframe.columns[:len(dataframe.columns) - 3]
full_dataframe = getFullDataframe(dataframe, df_baseline, columns)

try:
    full_dataframe.to_csv(path + "\\full_dataframe.csv", sep=";")
    print(f"Full Dataframe saved to {path}.")
except Exception as e:
    print(f"An error occurred saving the Full Dataframe: {e}")

# """Input Data for Models"""
# X = np.array(dataframe[columns])
# Y = np.array(dataframe[["Category"]])
#
# """Models Parameters for GridSearch"""
#
# param_grids = {
#     "KNN": {
#         'model': [neighbors.KNeighborsClassifier()],
#         'model__n_neighbors': list(range(1, 5)),
#         'model__weights': ['uniform', 'distance'],
#         'model__algorithm': ['auto', 'ball_tree', 'kd_tree', 'brute']
#     },
#     "SVM": {
#         'model': [svm.SVC(probability=True)],
#         'model__C': [0.1, 1, 10],
#         'model__kernel': ['linear', 'rbf'],
#         'model__gamma': ["scale", "auto"],
#         'model__random_state': list(range(0, 50, 2))
#     },
#     "Bayes": {
#         'model': [naive_bayes.GaussianNB()]
#     },  # No parameters for GaussianNB
#
#     "Logistic Regression": {
#         'model': [LogisticRegression()],
#         'model__C': [0.1, 1, 10],
#         'model__solver': ['lbfgs', 'newton-cg', 'sag', 'saga'],
#         'model__multi_class': ["multinomial"],
#         'model__random_state': list(range(0, 50, 5))
#     },
#     "Random Forest": {
#         'model': [ensemble.RandomForestClassifier()],
#         'model__n_estimators': [50, 100, 150],
#         'model__criterion': ["gini", "entropy", "log_loss"],
#         'model__random_state': list(range(0, 50, 5))
#     },
#     "NN": {
#         'model': [MLPClassifier()],
#         'model__activation': ['identity', 'logistic', 'tanh', 'relu'],
#         'model__solver': ['lbfgs', 'sgd', 'adam'],
#         'model__random_state': list(range(0, 50, 5))
#     }
# }
#
# """Train Model using GridSearchCV"""
#
# best_models = {}
#
# # Loop through each model and parameter grid
# for model_name, param_grid in param_grids.items():
#     # Create the pipeline
#     pipeline = Pipeline([
#         ('imputer', SimpleImputer(missing_values=np.nan, strategy="mean")),
#         ('scaler', StandardScaler()),
#         ('feature_selection', feature_selection.RFE(ensemble.RandomForestClassifier(random_state=42), step=1)),
#         ('model', param_grid['model'][0])  # Placeholder model to set pipeline structure
#     ])
#
#     # Grid search for hyperparameter tuning
#     if param_grid:
#         grid_search = GridSearchCV(
#             pipeline, param_grid, cv=5, n_jobs=-1, scoring='accuracy')
#         grid_search.fit(X, Y.ravel())
#
#         # Store the best model and score
#         best_models[model_name] = {
#             'best_estimator': grid_search.best_estimator_,
#             'best_score': grid_search.best_score_
#         }
#         print(f"Best cross-validation accuracy for {model_name}: {grid_search.best_score_:.4f}")
#     else:
#         # Fit the pipeline without grid search if no parameters
#         pipeline.fit(X, Y.ravel())
#         best_models[model_name] = {
#             'best_estimator': pipeline,
#             'best_score': pipeline.score(X, Y.ravel())  # Evaluate the score directly
#         }
#         print(f"No hyperparameters to tune for {model_name}. Model fitted directly.")
#
# # Sort the models by their best score in descending order
# sorted_models = sorted(best_models.items(), key=lambda item: item[1]['best_score'], reverse=True)
#
# # Select the top two models
# best_two_models = sorted_models[:2]
#
# estimators = [(model_name, info['best_estimator']) for model_name, info in best_two_models]
#
# # Create a VotingClassifier with the best two models
# voting_clf = VotingClassifier(estimators=estimators, voting='soft')  # You can also use 'hard' voting
# voting_clf.fit(X, Y.ravel())
#
# try:
#     joblib.dump(voting_clf, f"{path}/model.pkl")
#     print(f'VotingClassifier saved successfully to {path}')
# except Exception as e:
#     print(f'Error saving the model: {e}')
