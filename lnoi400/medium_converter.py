import numpy as np
import matplotlib.pyplot as plt
import tidy3d as td
from tidy3d.plugins.dispersion import FastDispersionFitter, AdvancedFastFitterParam

td.config.logging_level = "ERROR"


def fit(name, lda, n_data, eps_inf=None):
    fitter = FastDispersionFitter(wvl_um=lda, n_data=n_data)

    medium, err = fitter.fit(
        min_num_poles=3,
        max_num_poles=8,
        eps_inf=eps_inf,
        advanced_param=AdvancedFastFitterParam(show_progress=False),
    )

    n, k = medium.nk_model(td.C_0 / np.array(lda))
    plt.plot(lda, n_data, ".")
    plt.plot(lda, n)
    plt.show()

    print(
        f"""# RMS error: {err:.2g}
{name}_fit = td.PoleResidue(
    frequency_range=(td.C_0 / {max(lda)}, td.C_0 / {min(lda)}),
    eps_inf={medium.eps_inf},
    poles=("""
    )
    for pole in medium.poles:
        print(f"        {pole},")
    print("    )\n)")

    assert err < 1e-6
    return medium


lda = np.linspace(0.5, 2.0, 301)
lda2 = lda**2

e = 1.834
a = 3.0
b = 0.20315
n_data = np.sqrt(e + a * lda2 / (lda2 - b**2))

_ = fit("ln_o", lda, n_data, e)


e = 2.513
a = 2.0
b = 0.21738
n_data = np.sqrt(e + a * lda2 / (lda2 - b**2))

_ = fit("ln_e", lda, n_data, e)
