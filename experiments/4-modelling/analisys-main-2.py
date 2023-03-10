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


from semopy.effects import EffectStatic , EffectMA


def fa_analisys(data):
    cols = [ 'cb', 'traffic', 'retry_attempt', 'retry_interval', 'pc_succ_req', 'pc_fail_req', 'pc_cb_req', 'pc_c_rt']
    subset = data[cols]
    n_components = 3 # set the number of factors to extract
    fa = FactorAnalysis(n_components=n_components)
    X_transformed = fa.fit_transform(subset)

    # Get the factor loadings
    factor_loadings = fa.components_

    # Get the explained variance ratio for each factor
    explained_variance_ratio = fa.noise_variance_
    print(cols)
    print("Factor Loadings:\n", factor_loadings)
    print("Explained Variance Ratio for each factor:\n", explained_variance_ratio)

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
    # congestion =~ traffic
    # service_time =~  congestion
    # traffic_intercept =~   traffic   
    # retry_intercept =~ retry_attempt 
    # retry_i_intercept =~ retry_interval 
    # cb_intercept =~ cb
    # err =~ traffic + retry_attempt + retry_interval + cb
    
    
    pc_c_rt ~ traffic + retry_attempt + retry_interval + cb 
    pc_succ_req ~ retry_attempt + traffic + retry_interval + cb  
    pc_fail_req ~ retry_attempt + traffic + retry_interval + cb  
    pc_cb_req ~ retry_attempt + traffic  + cb  + retry_interval 



    pc_c_rt ~~ pc_succ_req 
    pc_c_rt ~~ pc_cb_req
    pc_c_rt ~~ pc_fail_req 
    pc_fail_req ~~ pc_succ_req
    pc_fail_req ~~ pc_cb_req 
    pc_succ_req ~~ pc_cb_req 
    """
    mod_2 = """
    # laten_1 =~  pc_fail_req 
    # laten_2 =~ pc_c_rt
    # laten_3 =~ pc_cb_req
    # congestion =~ pc_fail_req
    # congestion =~ pc_cb_req + pc_c_rt 

    # laten_1 =~ pc_cb_req 
    # laten_2 =~ pc_fail_req

    # pc_c_rt ~ traffic + retry_attempt + retry_interval + cb 
    # pc_succ_req ~ retry_attempt + traffic + retry_interval + cb  
    # pc_fail_req ~ retry_attempt + traffic + retry_interval + cb  
    # pc_cb_req ~ retry_attempt + traffic  + cb  + retry_interval 

    f_c_rt ~ pc_succ_req + pc_fail_req + pc_c_rt + retry_attempt 
    f_succ_req ~  pc_succ_req + pc_fail_req + pc_cb_req + retry_interval   
    f_fail_req ~ pc_c_rt + pc_succ_req + pc_cb_req  + pc_fail_req  + retry_attempt 

    # pc_c_rt ~~ pc_succ_req 
    # pc_c_rt ~~ pc_cb_req
    # pc_c_rt ~~ pc_fail_req 
    # pc_fail_req ~~ pc_succ_req
    # pc_fail_req ~~ pc_cb_req 
    # pc_succ_req ~~ pc_cb_req
    # f_c_rt ~~ f_succ_req
    # f_c_rt ~~ f_fail_req
    # f_fail_req ~~ f_succ_req
    


    """

    model = sem.Model(mod_2, )
    inputs = data[['cb', 'traffic', 'retry_attempt', 'retry_interval']]

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

    indices = ['traffic',  'retry_attempt',  'retry_interval', 'cb',  'pc_succ_req',  'pc_fail_req',  'pc_cb_req',   'pc_c_rt',  'f_succ_req',  'f_fail_req',  'f_cb_req',    'f_c_rt']
    dataframe = pd.DataFrame(data=covFull,index=indices, columns=indices )
    # data = data[['pc_c_rt','pc_succ_req', 'pc_fail_req', 'pc_cb_req', 'cb', 'traffic', 'retry_attempt', 'retry_interval']]
    # model.fit(data=None, obj="MLW", solver="SLSQP", cov=dataframe, n_samples=1000)

    # predicted = model.predict(data[['traffic',  'retry_attempt',  'retry_interval', 'cb',  'pc_succ_req',  'pc_fail_req',  'pc_cb_req',   'pc_c_rt', ]])
    # print(predicted)
    # print(predicted, data[['traffic',  'retry_attempt',  'retry_interval', 'cb',  'pc_succ_req',  'pc_fail_req',  'pc_cb_req',   'pc_c_rt', ]])
    #calculate_errors(data[['traffic',  'retry_attempt',  'retry_interval', 'cb',  'pc_succ_req',  'pc_fail_req',  'pc_cb_req',   'pc_c_rt', ]], predicted)
    # n_variables = len(data.columns)
    # df_model = n_variables * (n_variables + 1) / 2
    # df_residuals = len(data) - n_variables
    # df_total = len(data) - 1

    # # Calculate chi-squared and p-value
    # chi_squared = np.sum((data - predicted)**2)
    # p_value = 1 - sem.stats.chi2.cdf(chi_squared, df_residuals)

    # # Calculate CFI
    # cfi = 1 - (chi_squared + df_model) / (chi_squared + df_total)

    # # Calculate RMSEA
    # rmsea = np.sqrt(np.maximum(0, (chi_squared - df_residuals) / (df_residuals * df_total)))

    # # Calculate SRMR
    # srmr = np.sqrt(np.sum(np.square(predicted - data)) / (df_residuals * (n_variables - 1)))

    # print(f"CFI: {cfi}")
    # print(f"RMSEA: {rmsea}")
    # print(f"SRMR: {srmr}")

    model.fit(data=data, obj='MLW', solver='SLSQP')
    # sem.bias_correction( model , n=1000)
    
    results = model.inspect(mode='list', what="est", std_est=True)
    print(results)
    results = results.round(2)
    # for index, row in results.iterrows():
    #     print(row['lval'], '  &  ',row['op'], '  &  ',row['rval'], '  &  ',row['Estimate'], '  &  ',row['Est. Std'], '  &  ',row['Std. Err'], '  &  ',row['z-value'], '  &  ',row['p-value'], ' \\\ \hline  ')
    results = sem.calc_stats(model)
    for index, row in results.iterrows():
        print(row)
    print('division', results['chi2'][0]/results['DoF'][0])
    g = sem.semplot(model, "model2.pdf", plot_covs=True)

    # import numpy as np
    # mape = np.mean(sem.utils.compare_results(model, params ))
    # print('MAPE : {:.2 f}% '.format( mape * 100))



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

data = pd.read_csv("./datasets/exp4-main-2.csv")


data['pc_c_rt'] = data['pc_c_rt'].fillna(0)
data['f_c_rt'] = data['f_c_rt'].fillna(0)



# data_ol = remove_outliers(data,columns=['pc_c_rt','pc_succ_req', 'pc_fail_req', 'pc_cb_req', 'f_c_rt','f_succ_req', 'f_fail_req'], n_std=3)

# data_ol = (data-data.min())/(data.max()-data.min())

corr_matrix = data.corr()

calculate_sem(data, corr_matrix)

# fa_analisys(data)

#curve_fitting(data)



# def func(X, a, b, c, d, e):
#     cb,retry_attempt,retry_interval, traffic = X
#     return  a*cb + b*retry_attempt + c*retry_interval + d*traffic +e 


# x1 = np.array(data['cb'].to_list())
# x2 = np.array(data['retry_attempt'].to_list())
# x3 = np.array(data['retry_interval'].to_list())
# x4 = np.array(data['traffic'].to_list())
# y = np.array(data['pc_c_rt'].to_list())
# y_list = data_ol['pc_c_rt'].to_list()
# X = (x1, x2, x3, x4)
# X = data_ol[['traffic', 'retry_attempt', 'retry_interval', 'cb']]

# y = data_ol[['pc_succ_req', 'pc_fail_req', 'pc_cb_req', 'pc_c_rt']]


# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
# y_pred = multiple_regression(X_train, y_train, X_test)




# p0 = 0.7183, 0.0678, -6.7649, 0.0002 , -0.5947

# popt, pcov =curve_fit(func, X, y, p0)

# print(*popt)

# calculate_errors(y_test,y_pred)