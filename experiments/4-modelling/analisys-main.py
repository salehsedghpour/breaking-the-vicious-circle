import semopy as sem
import pandas as pd
import numpy as np
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, make_scorer, explained_variance_score, mean_squared_log_error, median_absolute_error, matthews_corrcoef
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from scipy.stats import zscore
from sklearn.neural_network import MLPRegressor
from sklearn.decomposition import PCA, FactorAnalysis
import matplotlib.pyplot as plt
from sklearn.svm import LinearSVC



def calculate_sem(data, corr_matrix):
    mod = """
    # latent variables

    # regression
    #pc_succ_req ~ retry_attempt + traffic
    #pc_fail_req ~ retry_attempt + retry_interval
    #pc_cb_req ~ cb + traffic + retry_attempt + retry_interval
    # pc_c_rt ~ retry_attempt + traffic
    f_succ_req ~ traffic + pc_succ_req + retry_interval
    f_fail_req ~ traffic + pc_fail_req + pc_cb_req
    f_c_rt ~ pc_c_rt + traffic

    # covariances
    #f_c_rt ~~ pc_c_rt + retry_interval
    #f_fail_req ~ pc_fail_req + pc_cb_req 

    """

    mod = """
    # latent variables
    # service_time =~ pc_c_rt 

    # regression
    pc_succ_req ~ retry_attempt  + traffic 
    pc_fail_req ~ traffic +  retry_attempt + retry_interval
    pc_cb_req ~ cb  + traffic + retry_attempt
    # pc_c_rt ~ retry_interval
    # covvariance
    #pc_c_rt ~~ retry_interval
    """

    """
    The following is a working model but the chi2 had issue:
    DoF                  35.000000
    DoF Baseline         59.000000
    chi2               1830.252252
    chi2 p-value          0.000000
    chi2 Baseline    312541.731654
    CFI                   0.994255
    GFI                   0.994144
    AGFI                  0.990128
    NFI                   0.994144
    TLI                   0.990315
    RMSEA                 0.069383
    AIC                  61.656484
    BIC                 287.146714
    LogLik                0.171758
    
    """
    mod = """
    # latent variables
    service_time =~ pc_c_rt 

    # regression
   
    pc_succ_req ~ retry_attempt  + traffic + retry_interval 
    pc_fail_req ~  retry_attempt  + traffic  + retry_interval
    pc_cb_req ~ retry_attempt  + traffic + cb 
    pc_c_rt ~ retry_attempt  + traffic 

    f_succ_req ~ traffic + pc_succ_req + retry_interval  + pc_cb_req
    f_fail_req ~ traffic + pc_fail_req + pc_cb_req 
    f_c_rt ~ pc_c_rt + traffic + retry_interval + retry_attempt + pc_cb_req + pc_fail_req 
    # covvariance
    #pc_c_rt ~~ retry_interval
    """


    # """
    # For the following model, the results are:
    # DoF              2.300000e+01
    # DoF Baseline     5.900000e+01
    # chi2             8.229953e+01
    # chi2 p-value     1.341826e-08
    # chi2 Baseline    3.125417e+05
    # CFI              9.998102e-01
    # GFI              9.997367e-01
    # AGFI             9.993245e-01
    # NFI              9.997367e-01
    # TLI              9.995132e-01
    # RMSEA            1.555554e-02
    # AIC              8.598455e+01
    # BIC              3.987613e+02
    # LogLik           7.723304e-03
    # """

    # mod = """
    # # latent variables
    # #service_time =~ pc_c_rt 

    # # regression
   
    # pc_succ_req ~ retry_attempt  + traffic + retry_interval + pc_c_rt + pc_fail_req
    # pc_fail_req ~  retry_attempt  + traffic  + retry_interval + cb 
    # pc_cb_req ~ retry_attempt  + traffic + cb  + retry_interval + pc_succ_req + pc_fail_req
    # pc_c_rt ~ retry_attempt   + pc_succ_req   

    # f_succ_req ~ traffic + pc_succ_req + retry_interval  + pc_cb_req + f_c_rt + f_fail_req
    # f_fail_req ~ traffic + pc_fail_req + pc_cb_req + retry_interval 
    # f_c_rt ~ pc_c_rt + traffic + retry_interval + retry_attempt + pc_cb_req + pc_fail_req + pc_succ_req  + f_succ_req + f_fail_req 
    # # covvariance
    # #pc_c_rt ~~ retry_interval
    # """

    mod = """
    # latent
    service_time =~ pc_c_rt
    retries =~ pc_cb_req + pc_succ_req + pc_fail_req

    # regression
    pc_succ_req ~  traffic + retry_attempt + retry_interval
    pc_fail_req ~  traffic + retry_attempt + retry_interval  + cb
    pc_cb_req ~  traffic + retry_attempt + cb 
    pc_c_rt ~ retry_attempt
    service_time ~ traffic  + pc_cb_req + retry_attempt
    retries ~ retry_attempt  + traffic  + cb + retry_interval

    # cov
     pc_succ_req ~~ pc_fail_req
    #pc_cb_req ~~ pc_fail_req


    """

    mod = """
    # initial intercepts
    #err =~  pc_c_rt

    # retries =~ pc_fail_req + pc_cb_req 
    

    pc_c_rt ~ traffic + retry_attempt + retry_interval + cb  
    pc_succ_req ~ retry_attempt + traffic + retry_interval  + cb 
    pc_fail_req ~ retry_attempt + traffic + retry_interval + cb 
    pc_cb_req ~ retry_attempt + traffic  + cb  + retry_interval



    pc_c_rt ~~ pc_succ_req
    pc_c_rt ~~ pc_cb_req
    pc_c_rt ~~ pc_fail_req 
    pc_fail_req ~~ pc_succ_req
    pc_fail_req ~~ pc_cb_req 
    pc_succ_req ~~ pc_cb_req 
    # pc_c_rt ~~ pc_succ_req + pc_cb_req + pc_fail_req

    # pc_fail_req ~~ pc_succ_req + pc_cb_req + pc_c_rt
    # pc_succ_req ~~ pc_c_rt + pc_cb_req + pc_fail_req 
    # pc_c_rt ~~ traffic + retry_attempt + retry_interval 
    # pc_succ_req ~~ retry_attempt + traffic + retry_interval  
    # pc_fail_req ~~ retry_attempt + traffic + retry_interval +cb
    # pc_cb_req ~~ retry_attempt + traffic  +cb



    """
    print(data.head(1))



    model = sem.Model(mod)
    model.fit(data, obj="MLW", solver="SLSQP", cov=corr_matrix)
    # Get the parameter estimates and intercept
    #coefficients = fit.get_standardized_coefficients()
    #intercept = fit.intercept_
    print(model.params_to_start)
    print(model.inspect(mode='list', what="est", std_est=True))

    results = sem.calc_stats(model)

    
    # with pd.option_context('display.max_rows', None,
    #                    'display.max_columns', None,
    #                    'display.precision', 3,
    #                    ):
    for index, row in results.iterrows():
        print(row)
    print(results)
    g = sem.semplot(model, "model.png", plot_covs=True)


def normalize(data, mode):
    if mode == 'scaler':
        scaler = StandardScaler()
        X_norm = scaler.fit_transform(data)
        return X_norm
    elif mode == 'minmax':
        scaler = MinMaxScaler()
        X_norm = scaler.fit_transform(data)
        return X_norm


def multiple_regression(X_train, y_train, X_test):
    # Create a linear regression model and fit it to the training data
    reg = LinearRegression()
    reg.fit(X_train, y_train)


    # Make predictions on the test data
    y_pred = reg.predict(X_test)


    # column_names = list(X_train.columns)

    # formula = "pc_c_rt = " + " + ".join([f"({coef:.9f})*"+column_names[i] for i, coef in enumerate(reg.coef_)])
    # formula += f" + ({reg.intercept_:.9f})"
    # print(formula)
    return y_pred
    

def calculate_errors(y_test, y_pred):
    # Evaluate the model using R-squared, MSE, and MAE
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)

    ev = explained_variance_score(y_test, y_pred)
    # msle = mean_squared_log_error(y_test, y_pred)
    med_a_e = median_absolute_error(y_test, y_pred)


    #accuracy = accuracy_score(y_test, y_pred)
    #precision = precision_score(y_test, y_pred)
    #f_1 = f1_score(y_test, y_pred)
    #recall = recall_score(y_test, y_pred)    
    # Print the results
    print('R-squared:', r2)
    print('Mean Squared Error (MSE):', mse)
    print('Root Mean Squared Error (RMSE):', rmse)
    print('Mean Absolute Error (MAE):', mae)
    print('Explained Variance (EV):', ev)
    # print('Mean Squared Logarithimic Error (MSLE):', msle)
    print('Median Absolute Error (MedAE):', med_a_e)
    #print('Accuracy:', accuracy)
    #print('Precision:', precision)
    #print('F-1:', f_1)
    #print('Recall:', recall)


def random_forest(X_train, y_train, X_test):
    # Train random forest model
    rf = RandomForestRegressor(n_estimators=500)
    rf.fit(X_train, y_train)

    # Make predictions on test set
    y_pred = rf.predict(X_test)
    return y_pred

def gradiant_boosting(X_train, y_train, X_test):
    # Create a Gradient Boosting Regression model and fit it to the training data
    gbr = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
    gbr.fit(X_train, y_train)

    # Use the model to make predictions on the testing data
    y_pred = gbr.predict(X_test)
    return y_pred

def rf_grid_search(X_train, y_train,):
    # Define the random forest regressor
    rf = RandomForestRegressor()

    # Define the parameter grid to search
    param_grid = {
        'n_estimators': [50, 100, 200, 300, 500, ],
        'max_depth': [5, 10, 15, 50],
        'min_samples_split': [2, 5,  100],
        'min_samples_leaf': [ 2,  32],
        #'max_features': ['auto', 'sqrt', 'log2'],
        'criterion' :['mse', 'mae']

    }

    # Define the scoring metric (in this case, mean squared error)
    scoring = make_scorer(mean_squared_error)

    # Define the GridSearchCV object
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        scoring=scoring,
        cv=5,
        n_jobs=-1
    )

    # Fit the grid search object to the data
    grid_search.fit(X_train, y_train)

    # Print the best parameters and best score
    print("Best parameters:", grid_search.best_params_)
    print("Best score:", grid_search.best_score_)





# read and clean data
data = pd.read_csv("./datasets/exp4-main.csv")
mapping_cb = {'none': 1024, 1: 1, 50: 50, 100: 100, 1024: 1024}
mapping_retry = {'none' : 2, '1': 1, '5': 5, '10': 10}
data['cb'] = data['cb'].apply(lambda x: mapping_cb[x])
data['retry_attempt'] = data['retry_attempt'].apply(lambda x: mapping_retry[x])
data['pc_c_rt'] = data['pc_c_rt'].fillna(0)
data['f_c_rt'] = data['f_c_rt'].fillna(0)
data = data.astype(float)

data.to_csv("my_ds.csv")





# # calculate the z-scores
# data_zscore = data.apply(zscore)

# # set a threshold for removing outliers
# threshold = 3

# # find the indices of the outliers
# outlier_indices = np.where(data_zscore > threshold)
# print(outlier_indices)

# # remove the outliers from the dataset
# clean_data = data[(data_zscore < threshold).all(axis=1)]
# print(len(clean_data))

# corr_matrix = data.corr()


# #data = data[['traffic' , 'retry_attempt' , 'retry_interval', 'cb', 'f_succ_req', 'f_fail_req', 'f_c_rt']]
# sorted_corr = corr_matrix.abs().unstack().sort_values(kind="quicksort").reset_index()
# sorted_corr = sorted_corr[sorted_corr["level_0"] != sorted_corr["level_1"]]

# print(sorted_corr)
data['retry_interval'] = data['retry_interval'].div(1000).round(2)
data['f_c_rt'] = data['f_c_rt'].div(1000).round(2)
data['pc_c_rt'] = data['f_c_rt'].div(1000).round(2)

data['traffic'] = data['traffic'].mul(33).round(2)

# data = normalize(data,'minmax')


corr_matrix = data.corr()


# #data = data[['traffic' , 'retry_attempt' , 'retry_interval', 'cb', 'pc_succ_req', 'pc_fail_req', 'pc_c_rt', 'pc_cb_req', 'f_succ_req', 'f_fail_req', 'f_c_rt', ]]
# sorted_corr = corr_matrix.abs().unstack().sort_values(kind="quicksort").reset_index()
# sorted_corr = sorted_corr[sorted_corr["level_0"] != sorted_corr["level_1"]]

# sorted_corr.to_csv('test.csv')
# # Calculate the standard deviations of the variables
# std_devs = np.sqrt(np.diag(corr_matrix))

# # Create a StandardScaler object and fit it to the standard deviations
# scaler = StandardScaler()
# scaler.fit(std_devs.reshape(-1, 13))

# # Transform the correlation matrix to a covariance matrix
# cov_matrix = np.outer(std_devs, std_devs) * corr_matrix
# cov_matrix = scaler.scale_ * cov_matrix * scaler.scale_




X = data[['traffic', 'retry_attempt', 'retry_interval', 'cb']]

y = data[['pc_succ_req', 'pc_fail_req', 'pc_cb_req', 'pc_c_rt']]
# X = data[[ 'retry_interval','retry_attempt' , 'traffic', 'cb']]
# y = data[['f_succ_req']]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# # Normalize data
# scaler = StandardScaler()
# X_train = scaler.fit_transform(X_train)
# X_test = scaler.transform(X_test)

# y_pred = random_forest(X_train, y_train, X_test)



# # Train the MLP model
# model = MLPRegressor(hidden_layer_sizes=(2,20), activation='relu', solver='adam', alpha=0.001, max_iter=1000, random_state=42)
# model.fit(X_train, y_train)

# # Make predictions on the test set
# y_pred = model.predict(X_test)

# calculate_errors(y_test, y_pred)




calculate_sem(data, corr_matrix)

# import matplotlib.pyplot as plt
# plt.plot(X_test, y_test, label='Actual values')
# plt.plot(X_test, y_pred, label='Predicted values')
# plt.xlabel('X_test')
# plt.ylabel('Y values')
# plt.legend()
# plt.show()




