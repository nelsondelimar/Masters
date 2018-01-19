# -----------------------------------------------------------------------------------
# Title: Data Filtering
# Author: Nelson Ribeiro Filho
# Description: Source codes for potential field filtering
# Collaborator: Rodrigo Bijani
# -----------------------------------------------------------------------------------

# Import Python libraries
from __future__ import division
import warnings
import numpy as np
import auxiliars as aux
import derivative as deriv

def continuation(x, y, data, H):
    
    '''
    This function compute the upward or downward continuation for a potential field 
    data, which can be gravity or magnetic signal. The value for H represents the 
    level which the data will be continuated. If H is positive, the continuation is 
    upward, because Dz is greater than 0 and the exponential is negative; otherwise, 
    if H is negative, the continuation is downward.
    
    Input:
    x - numpy 2D array - observation points on the grid in X direction
    y - numpy 2D array - observation points on the grid in Y direction
    data - 2D array - gravity or magnetic data
    H - float - value for the new observation level
    
    '''
    assert H != 0., 'Height must be different of zero!'
    
    # calculate the wavenumbers
    kx, ky = aux.wavenumber(x, y)
    
    if H > 0.:
        #print ('H is positive. Continuation is Upward!')
        kcont = np.exp((-H) * np.sqrt(kx**2 + ky**2))
        result = kcont * np.fft.fft2(data)
    elif H < 0.:
        #print ('H is negative. Continuation is Downward!')
        kcont = np.exp((-H) * np.sqrt(kx**2 + ky**2))
        result = kcont * np.fft.fft2(data)

    # Return the final output
    return np.fft.ifft2(result)

def reduction(x, y, data, oldf, olds, newf, news):
    
    '''
    Return the reduced potential data giving the new directions for the geomagnetic
    field and source magnetization. Its based on Blakely (1996).
    
    Inputs: 
    x - numpy 2D array - coordinate at X
    y - numpy 2D array - coordinate at Y
    data - numpy 2D array - magnetic data set (usually total field anomaly)
    oldf - numpy 1D array - vector with old field directions
    olds - numpy 1D array - vector with old source directions
    newf - numpy 1D array - vector with new field directions
    news - numpy 1D array - vector with new source directions
    
    - The last four vector are discplaced as : v = [inc, dec]
    
    Output:
    res - numpy 2D array - result by using reduction filter
    
    Ps. This filter is very useful for values of incination greater than +/- 15 deg.
    '''

    # Conditions for X and Y grids
    if x.shape != y.shape != data.shape:
        raise ValueError("Input arrays x, y, and data must have the same shape!")
    #assert x.shape == y.shape, 'Grid in X and grid in Y must have same dimension!'
    #assert x.shape == data.shape, 'Grid in X and Data must have same dimension!'
    #assert y.shape == data.shape, 'Grid in X and Data must have same dimension!'
    
    # Conditions for all direction vectors
    assert olfd.size == newf.size, 'Vector must have only inclination and declination!'
    assert olfs.size == news.size, 'Vector must have only inclination and declination!'
    
    # Step 1 - Calculate the wavenumbers
    # It will return the wavenumbers in x and y directions, in order to calculate the
    # values for magnetization directions in Fourier domains:
    kx, ky = aux.wavenumber(x, y)
    
    # Step 2 - Calcuate the magnetization direction
    # It will return the magnetization directions in Fourier domain for all vector that
    # contain  inclination and declination. All values are complex.
    f0 = aux.theta(oldf, kx, ky)
    m0 = aux.theta(olds, kx, ky)
    f1 = aux.theta(newf, kx, ky)
    m1 = aux.theta(news, kx, ky)
       
    # Step 3 - Calculate the filter
    # It will return the result for the reduction filter. However, it is necessary use a
    # condition while the division is been calculated, once there is no zero division.
    with np.errstate(divide='ignore', invalid='ignore'):
        operator = (f1 * m1)/(f0 * m0)
    operator[0, 0] = 0.
    
    # Calculate the result by multiplying the filter and the data on Fourier domain
    res = operator*np.fft.fft2(data)
    
    # Return the final output
    return np.fft.ifft2(res)

def tilt(x, y, data):
    
    '''
    Return the tilt angle for a potential data on a regular grid.

    Inputs:
    x - numpy 2D array - grid values in x direction
    y - numpy 2D array - grid values in y direction
    data - numpy 2D array - potential data
    
    Output:
    tilt - numpy 2D array - tilt angle for a potential data
    '''
    
    # Stablishing some conditions
    assert x.shape == data.shape, 'Grid in X and data must have the same shape!'
    assert y.shape == data.shape, 'Grid in Y and data must have the same shape!'
    
    # Calculate the horizontal and vertical gradients
    hgrad = deriv.horzgrad(x, y, data)
    derivz = deriv.zderiv(x, y, data, 1)
    
    # Tilt angle calculation
    tilt = np.arctan2(derivz, hgrad)
    
    # Return the final output
    return tilt

def thetamap(x, y, data):

    '''
    Return the theta map transformed data.
    
    Inputs:
    x - numpy 2D array - grid values in x direction
    y - numpy 2D array - grid values in y direction
    data - numpy 2D array - potential data
    
    Output:
    thetamap - numpy 2D array - thetha map calculated
    '''
    
    # Stablishing some conditions
    assert x.shape == data.shape, 'Grid in X and data must have the same shape!'
    assert y.shape == data.shape, 'Grid in Y and data must have the same shape!'
    
    # Calculate the horizontal and total gradients
    hgrad = deriv.horzgrad(x, y, data)
    tgrad = deriv.totalgrad(x, y, data)
   
    # Return the final output
    return (hgrad/tgrad)

def hyperbolictilt(x, y, data):
    
    '''
    Return the hyperbolic tilt angle for a potential data.
    
    Inputs:
    x - numpy 2D array - grid values in x direction
    y - numpy 2D array - grid values in y direction
    data - numpy 2D array - potential data
    
    Output:
    hyptilt - numpy 2D array - hyperbolic tilt angle calculated
    '''
    
    # Stablishing some conditions
    assert x.shape == data.shape, 'Grid in X and data must have the same shape!'
    assert y.shape == data.shape, 'Grid in Y and data must have the same shape!'

    # Calculate the horizontal and vertical gradients
    hgrad = deriv.horzgrad(x, y, data)
    derivz = deriv.zderiv(x, y, data, 1)
    
    # Compute the tilt derivative
    hyptilt = np.arctan2(derivz, hgrad)
    
    # Return the final output
    return np.real(hyptilt)

def pseudograv(x, y, data, field, source, rho, mag):

    '''
    This function calculates the pseudogravity anomaly transformation due to a total 
    field anomaly grid. It recquires the X and Y coordinates (respectively North and 
    East directions), the magnetic data as a 2D array grid, the values for inclination 
    and declination for the magnetic field and the magnetization of the source.
    
    Inputs:
    x - numpy 2D array - coordinates in X direction
    y - numpy 2D array - coordinates in y direction
    data - numpy 2D array - magnetic data (usually total field anomaly)
    field - numpy 1D array - inclination and declination for the magnetic field
        field[0] -> inclination
        field[1] -> declination
    source - numpy 1D array - inclination and declination for the magnetic source
        source[0] -> inclination
        source[1] -> declination

    Output:
    pgrav - numpy array - pseudo gravity anomaly
    '''
    
    # Conditions (1):
    assert x.shape == data.shape, 'Grid in X and data must have the same shape!'
    assert y.shape == data.shape, 'Grid in Y and data must have the same shape!'
    
    # Conditions (2):
    field.size == source.size, 'Vectors for all directions must have same size!'
    
    # Conditions (3):
    assert rho != 0., 'Density must not be zero!'
    assert mag != 0., 'Density must not be zero!'
    
    # Conversion for gravity and magnetic data
    G = 6.673e-11
    si2mGal = 100000.0
    t2nt = 1000000000.0
    cm = 0.0000001
        
    # Compute the constant value
    C = G*rho*si2mGal/(cm*mag*t2nt)
    
    # Calculate the wavenumber
    kx, ky = aux.wavenumber(x, y)
    k = (kx**2 + ky**2)**(0.5)
    
    # Computing theta values for the source
    thetaf = aux.theta(field, kx, ky)
    thetas = aux.theta(source, kx, ky)
    
    # Calculate the product
    # Here we use the numpy error statement in order to evaluate the zero division
    with np.errstate(divide='ignore', invalid='ignore'):
        prod = 1./(thetaf*thetas*k)
    #prod[0, 0] = 0.
    
    # Calculate the pseudo gravity anomaly
    res = np.fft.fft2(data)*prod
    
    # Converting to mGal as a product by C:
    res *= C
    
    # Return the final output
    return np.fft.ifft2(res)