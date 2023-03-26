import semopy as sem
import pandas as pd
import numpy as np
from sklearn.decomposition import FactorAnalysis 
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from numpy.polynomial.chebyshev import chebval
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, make_scorer, explained_variance_score, mean_squared_log_error, median_absolute_error, matthews_corrcoef
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from scipy import stats
from statsmodels.stats.moment_helpers import corr2cov

from factor_analyzer import FactorAnalyzer



from semopy.effects import EffectStatic , EffectMA


def fa_analisys(data):
    data['pc_c_rt'] = data['pc_c_rt'].apply(lambda x: x*1000)
    data.drop('retry_interval', inplace=True, axis=1)
    data.drop('retry_attempt', inplace=True, axis=1)
    data.drop('traffic', inplace=True, axis=1)
    data.drop('cb', inplace=True, axis=1)

    from factor_analyzer.factor_analyzer import FactorAnalyzer 
    # from numpy.linalg import eig
    # w,v=eig()
    # print('E-value:', w)
    # print('E-vector', v)
    fa = FactorAnalyzer(2, rotation='varimax')

    fa.fit(data)

    
    # Check Eigenvalues
    ev, v = fa.get_eigenvalues()
    print(ev)
    print(pd.DataFrame(fa.loadings_, columns=['Factor1', 'Factor2'], index=data.columns))    
    # Results:
    """
                Factor1   Factor2   Factor3   Factor4
traffic         0.086181  0.070432  0.602389  0.091686
retry_attempt  -0.018713  0.670657 -0.101082  0.071243
retry_interval  0.674014 -0.051394 -0.099157 -0.002742
cb             -0.029688  0.015487 -0.000779 -0.172737
pc_succ_req     0.788825 -0.370923  0.140214  0.086159
pc_fail_req    -0.578177 -0.287935  0.745157 -0.167144
pc_cb_req      -0.065539  0.060165  0.042444  0.986787
pc_c_rt        -0.294583  0.779507  0.230518 -0.130623
pc_retried_req -0.435689  0.457828  0.474449 -0.073152
    factor1 = retry_interval + pc_succ_req + pc_fail_req + pc_c_rt + pc_retried_req # when the retry interval is too short
    factor2 = retry_attempt + pc_succ_req + pc_fail_req + pc_c_rt + pc_retried_req # when the number of retry increases 
    factor3 = traffic + pc_fail_req + pc_c_rt + pc_retried_req # overload
    factor4 = cb + pc_fail_req + pc_cb_req + pc_c_rt # sidecar congestion
    """


    # cols = [ 'cb', 'traffic', 'retry_attempt', 'retry_interval', 'pc_succ_req', 'pc_fail_req', 'pc_cb_req', 'pc_c_rt', 'pc_retried_req']
    # subset = data[cols]
    # n_components = 5 # set the number of factors to extract
    # fa = FactorAnalysis(n_components=n_components)
    # X_transformed = fa.fit_transform(subset)

    # # Get the factor loadings
    # factor_loadings = fa.components_

    # # Get the explained variance ratio for each factor
    # explained_variance_ratio = fa.noise_variance_
    # print(cols)
    # print("Factor Loadings:\n", factor_loadings)
    # print("Explained Variance Ratio for each factor:\n", explained_variance_ratio)

    # for factor in factor_loadings:

    #     for i in range(len(cols)):
    #         print(cols[i], factor[i])
    #     print("----------------------")

    # output
    """
    [ 'cb', 'traffic', 'retry_attempt', 'retry_interval']
    Factor Loadings:
    [[ 3.57322986e+02  3.16708885e-05  5.54906801e-05 -8.42647990e-08]
    [-1.06732738e-06 -3.19379564e-06  6.87289743e+00 -1.95950051e-06]
    [ 4.28881698e-10 -3.79482524e-04  7.93583995e-09  5.06151504e-05]]
    Explained Variance Ratio for each factor:
    [1.         0.07998893 1.         0.00142308]
    
    """

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



def calculate_sem(data, corr_matrix):
    mod_1 = """

    service_time =~ carriedResponseTime  
    # congestion =~ failureRate 

    # factor1 =~ retryRate + carriedResponseTime + successRate + failureRate
    # factor2 =~ circuitBrokenRate + failureRate

    
    carriedResponseTime ~    retryRate + traffic  + successRate + circuitBrokenRate + failureRate
    successRate ~ retryAttempt + traffic + retryPerTryTimeout + retryRate
    failureRate ~  traffic + retryPerTryTimeout  + circuitBrokenRate + retryRate
    circuitBrokenRate ~  traffic  + circuitBreakerMaxRequests   
    retryRate ~ retryAttempt    + failureRate

    """
    # data['pc_c_rt'] = data['pc_c_rt'].apply(lambda x: x*1000)

    model = sem.Model(mod_1 )
   
    corr_mat = data.corr()
    std_data = data.std(axis=0)

    covMatrix = corr2cov(corr_mat, std_data)

    X = np.tril(np.array(covMatrix))
    X_low = np.tril(X)
    X_low = X_low.T
    for ind, i in enumerate(X_low):
        for ind2, j in enumerate(i):
            if(ind == ind2):
                X_low[ind][ind2]=0
    covFull = X+X_low

    indices = ['traffic',  'retryAttempt',  'retryPerTryTimeout', 'circuitBreakerMaxRequests',  'successRate',  'failureRate',  'circuitBrokenRate',   'carriedResponseTime', 'retryRate',]#  'f_succ_req',  'f_fail_req',  'f_cb_req',    'f_c_rt']
    dataframe = pd.DataFrame(data=covFull,index=indices, columns=indices )
    # data = data[['pc_c_rt','pc_succ_req', 'pc_fail_req', 'pc_cb_req', 'cb', 'traffic', 'retry_attempt', 'retry_interval']]
    model.fit(data=None, obj="MLW", solver="SLSQP", cov=dataframe, n_samples=200)



    # model.fit(data=data, obj='MLW', solver='SLSQP')
    
    results1 = model.inspect(mode='list', what="est", std_est=True)
    print(results1)
    # for index, row in results.iterrows():
    #     print(row['lval'], '  &  ',row['op'], '  &  ',row['rval'], '  &  ',row['Estimate'], '  &  ',row['Est. Std'], '  &  ',row['Std. Err'], '  &  ',row['z-value'], '  &  ',row['p-value'], ' \\\ \hline  ')
    results = sem.calc_stats(model)
    for index, row in results.iterrows():
        print(row)
    print('division', results['chi2'][0]/results['DoF'][0])
    g = sem.semplot(model, "model3.pdf")



def curve_fitting(data):



    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from scipy.optimize import curve_fit
    from numpy.polynomial import chebyshev

    # Define the Chebyshev fit function for multiple independent variables
    def chebyshev_fit(X, *p):
        """
        Chebyshev fit function for multiple independent variables.

        Parameters:
        X (array-like): independent variables
        p (array-like): Chebyshev coefficients

        Returns:
        y (array-like): dependent variable
        """
        # Compute Chebyshev basis functions for each independent variable
        basis_funcs = [chebyshev.chebval(X[:, i], np.arange(len(p))) for i in range(X.shape[1])]

        # Compute the weighted sum of the basis functions
        y = p[0]
        for i in range(X.shape[1]):
            y += p[i+1] * basis_funcs[i]

        return y

    # Load the data

    # Extract the independent and dependent variables
    x1 = np.array(data['cb'].to_list())
    x2 = np.array(data['retry_attempt'].to_list())
    x3 = np.array(data['retry_interval'].to_list())
    x4 = np.array(data['traffic'].to_list())
    y = np.array(data['pc_c_rt'].to_list())
    X = np.column_stack((x1, x2, x3, x4))
    # combine the independent variables into one array
    X = np.column_stack((x1, x2, x3, x4))

    # Fit the data using Chebyshev polynomial fit
    p0 = np.zeros((X.shape[1]+1,))
    popt, pcov = curve_fit(chebyshev_fit, X, y, p0)
    plt.plot(X, chebyshev_fit(X, *popt), 'g--')
    plt.show()


    # Create Chebyshev object using the obtained coefficients
    fitted_curve = np.polynomial.chebyshev.Chebyshev(popt)

    # Print the final formula
    print(fitted_curve)
    



def remove_outliers(df,columns,n_std):
    for col in columns:
        print('Working on column: {}'.format(col))
        
        mean = df[col].mean()
        sd = df[col].std()
        
        df = df[(df[col] <= mean+(n_std*sd))]
        
    return df


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

data = pd.read_csv("./datasets/test.csv")

# print(data)

data['pc_c_rt'] = data['pc_c_rt'].fillna(0)
data['f_c_rt'] = data['f_c_rt'].fillna(0)
data.drop('f_cb_req', inplace=True, axis=1)
data.drop('f_succ_req', inplace=True, axis=1)
data.drop('f_fail_req', inplace=True, axis=1)
data.drop('f_c_rt', inplace=True, axis=1)

z = np.abs(stats.zscore(data))
data = data[(z < 3).all(axis=1)].reset_index()
data.drop('index', inplace=True, axis=1)
# print(np.isnan(data).any())

data.rename(columns= {'retry_attempt':'retryAttempt', 'retry_interval':'retryPerTryTimeout', 'cb':'circuitBreakerMaxRequests', 'pc_succ_req':'successRate', 'pc_fail_req':'failureRate', 'pc_cb_req':'circuitBrokenRate', 'pc_c_rt': 'carriedResponseTime', 'pc_retried_req':'retryRate'}, inplace=True)

print(data)

data.to_csv("./datasets/test-outlier.csv")
# print(np.isinf(data).any())


# fa_analisys(data)

# data_ol = remove_outliers(data,columns=['pc_c_rt','pc_succ_req', 'pc_fail_req', 'pc_cb_req', 'f_c_rt','f_succ_req', 'f_fail_req'], n_std=3)

# data_ol = (data-data.min())/(data.max()-data.min())

corr_matrix = data.corr()

calculate_sem(data, corr_matrix)

