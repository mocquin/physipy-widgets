from numpy import pi

import ipywidgets as ipyw
from ipywidgets import Layout

import traitlets
from traitlets import TraitError

from physipy import quantify, Dimension, Quantity, units, set_favunit, DimensionError, dimensionify
from physipy.quantity.dimension import DIMENSIONLESS

class QuantityText(ipyw.Box, ipyw.ValueWidget, ipyw.DOMWidget):
    """

    """

    # dimension trait : a Dimension instance
    # use to store the dimension at startup and check
    # if new value has same dimension when same dimension
    # is mandatory through fixed_dimension
    # does the dimension needs to be a trait ?
    # using lookup as a property on the value is enough ?
    # dimension = traitlets.Instance(Dimension, allow_none=False)
    # does not make sense to make this a dimension since dimension
    # should never be changed inplace, and so using value to observe/validate
    # should be enough
    @property
    def dimension(self): return self.value.dimension

    # value trait : a Quantity instance
    value = traitlets.Instance(Quantity, allow_none=False)

    # favunit : a quantity or None
    # this is only used for display purpose
    favunit = traitlets.Instance(Quantity, allow_none=True)

    # at __new__, all these attributes are traitlets.Undefined

    def __init__(self,
                 value=0.0,
                 disabled=False,
                 continuous_update=True,
                 description="Quantity:",
                 fixed_dimension=False,
                 placeholder="Type python expr",
                 favunit=None,
                 add_context={},
                 **kwargs):

        # context for parsing
        self.context = {**units, "pi": pi, **add_context}

        # set text widget
        self.text = ipyw.Text(
            value="",
            placeholder=placeholder,
            description=description,
            disabled=disabled,
            continuous_update=continuous_update,
            layout=Layout(width='auto',
                          margin="0px 0px 0px 0px",
                          padding="0px 0px 0px 0px",
                          border="solid gray"),
            style={'description_width': '130px'},
        )

        # quantity work
        # set dimension
        value = quantify(value)
        self.fixed_dimension = fixed_dimension

        if favunit is not None:
            value.favunit = favunit

        # set quantity
        self.value = value

        # set text value after setting the favunit
        self.text.value = str(self.value)

        # Actually a Box widget that wraps a Text widget
        super().__init__(**kwargs)
        self.children = [self.text]

        # on_submit observe : what to do when text is entered
        def text_update_values(wdgt):

            # get expression entered
            expression = wdgt.value
            expression = expression.replace(
                " ", "*")  # to parse "5 m" into "5*m"

            # eval expression with unit context
            try:
                res = eval(expression, self.context)
                res = quantify(res)
                self.value = res
                self.update_text()
            except BaseException:
                # if anything fails, do nothing
                # self.value.favunit is used here
                self.update_text()

        # create the callback
        self.text.on_submit(text_update_values)

    def update_text(self):
        self.text.value = str(self.value)

    @property
    def description(self):
        """
        Used by interact/interactive.
        """
        return self.text.description

    # update text on quantity value change
    @traitlets.observe("value")
    def _update_display_val(self, proposal):
        # 
        # update favunit if applicable
        if self.favunit is None and self.value.favunit is not None:
            self.favunit = self.value.favunit
        else:
            # handle 5*mm to 5*s
            if self.favunit is not None:
                if self.favunit.dimension != self.value.dimension:
                    self.favunit = None
                # if the dimension is the same, we keep the previous favunit
                else:
                    self.value.favunit = self.favunit

        self.update_text()
        # now set text with favunit set
        # self.value.favunit is used here
        #self.text.value = f'{str(self.value)}'


    @traitlets.observe("favunit")
    def _update_display_val_on_favunit_change(self, proposal):
        #self.value.favunit is used here
        # self.text.value = f'{str(self.value)}'
        self.update_text()

    # helper to validate value the value if fixed dimension

    @traitlets.validate('value')
    def _valid_value(self, proposal):
        # try to cast the proposal value to a Quantity
       # if not isinstance(proposal["value"], Quantity):
       #     proposal["value"] = quantify(proposal['value'])
        try:
            current_dimension = self.dimension
        except TraitError as e:
            # at init, no self.value, so no self.dimension so we allow the proposed value
            return proposal['value']
        if self.fixed_dimension and (proposal['value'].dimension != current_dimension):
            raise TraitError(
                    'Dimension between old and new value should be consistent for fidex_dimension=True.')
        return proposal['value'] # after this return, the value is set and all 
        

    # observers are called

    @traitlets.validate("favunit")
    def _valid_favunit(self, proposal):
        favunit = proposal['value']
        if favunit is None and self.value.favunit is None:
            # we fall back on the passed quantity's favunit
            # (that could be None also)
            return self.value._pick_smart_favunit()
        else:
            self.value.favunit = favunit
            return favunit

        # TODO : link those 2
        # self.value.favunit = self.favunit


class FDQuantityText(QuantityText):
    """
    A FDQuantityText simply wraps QuantityText with fixed_dimension to True,
    making it even more explicit that the dimension can't be changed.
    """

    def __init__(self, *args, **kwargs):

        # pop the fixed_dimension kwarg if present
        # and raise Error if it was False
        # forgive if was True
        fixed_dimension = kwargs.get("fixed_dimension", True)
        if not fixed_dimension:
            raise ValueError(
                "fixed_dimension can't be False. Use QuantityText.")

        # Set it to true and send to QuantityText
        kwargs["fixed_dimension"] = True
        super().__init__(*args,
                         **kwargs)


class QuantitySlider(ipyw.Box, ipyw.ValueWidget, ipyw.DOMWidget):
    """
    A slider wrapped in a box to the stores the numerical value,
    and exposes a value that is the Quantity.
    """

    # dimension trait : a Dimension instance
    # dimension = traitlets.Instance(Dimension, allow_none=False)
    # value trait : a Quantity instance
    value   = traitlets.Instance(Quantity, allow_none=False)
    favunit = traitlets.Instance(Quantity, allow_none=True)

    # what the point of those being declared here ? except enforcing
    # to be quantity ?
    qmin  = traitlets.Instance(Quantity, allow_none=False)
    qmax  = traitlets.Instance(Quantity, allow_none=False)
    qstep = traitlets.Instance(Quantity, allow_none=False)

    @property
    def dimension(self): return self.value.dimension

    def __init__(self, value=None, min=None, max=None, step=None, disabled=False,
                 continuous_update=True, description="Quantity:",
                 # placeholder="Type python expr",
                 fixed_dimension=False, label=True, favunit=None,
                 **kwargs):

        super().__init__(**kwargs)
        self.fixed_dimension = fixed_dimension

        if value is not None:
            value = quantify(value)
        if min is not None:
            min   = quantify(min)
        if max is not None:
            max   = quantify(max)
        if step is not None:
            step  = quantify(step)

        if min is None and value is not None:
            min = Quantity(0.0, value.dimension)
        if max is None and value is not None:
            max = Quantity(100.0, value.dimension)
        if step is None and value is not None:
            step = Quantity(0.1, value.dimension)

        if favunit is not None:
            value.favunit = favunit

        

        # handle None value
        if value is not None:
            value = quantify(value)
        elif min is not None:
            value = min * 1  # to reset favunit
        else:
            value = quantify(0.0)


        # set slider widget
        self.slider = ipyw.FloatSlider(value=value.value,
                                       min=min.value,
                                       max=max.value,
                                       step=step.value,
                                       description=description,
                                       disabled=disabled,
                                       continuous_update=continuous_update,
                                       # orientation=orientation,
                                       readout=False,  # to disable displaying readout value
                                       # readout_format=readout_format,
                                       # layout=Layout(width="50%",
                                       #              margin="0px",
                                       #              border="solid red"),
                                       )
        
        # set quantity
        self.value = value

        # validate min
        if min is not None:
            qmin = quantify(min)
            if not qmin.dimension == self.value.dimension:
                raise DimensionError(qmin.dimension, self.value.dimension)
        else:
            qmin = Quantity(0.0, self.value.dimension)

        # validate max value
        if max is not None:
            qmax = quantify(max)
            if not qmax.dimension == self.value.dimension:
                raise DimensionError(qmax.dimension, self.value.dimension)
        else:
            qmax = Quantity(100.0, self.value.dimension)

        # validate step value
        if step is not None:
            qstep = quantify(step)
            if not qstep.dimension == self.value.dimension:
                raise DimensionError(qstep.dimension, self.value.dimension)
        else:
            qstep = Quantity(0.1, self.value.dimension)

        self.qstep = qstep
        self.qmin  = qmin
        self.qmax  = qmax

        # observe slider value : for interaction with the widget
        def update_label_on_slider_change(change):
            self.value = Quantity(
                change.new, self.value.dimension, favunit=self.favunit)
            self.label.value = str(self.value)
        self.slider.observe(update_label_on_slider_change, names="value")

        # observe self.value : when using the OOP interaction
        def update_slider_value(change):
            self.slider.value = change.new.value
        self.observe(update_slider_value, names="value")

        # display the quantity value of the slider in label
        self.label = ipyw.Label(value=str(self.value))

        if label:
            self.children = [
                self.slider,
                self.label,
            ]
        else:
            self.children = [
                self.slider,
            ]

    @property
    def description(self):
        """
        Also used in QuantityText
        """
        return self.slider.description

    @traitlets.observe("value")
    def _update_display_val(self, proposal):
        # 
        # update favunit if applicable
        if self.favunit is None and self.value.favunit is not None:
            self.favunit = self.value.favunit
        else:
            # handle 5*mm to 5*s
            if self.favunit is not None:
                if self.favunit.dimension != self.value.dimension:
                    self.favunit = None
                # if the dimension is the same, we keep the previous favunit
                else:
                    self.value.favunit = self.favunit

    @traitlets.validate('value')
    def _valid_value(self, proposal):
        if self.fixed_dimension and proposal['value'].dimension != self.dimension:
            raise TraitError(
                'Dimension between old and new value should be consistent.')
        return proposal['value']
    

    @traitlets.validate("favunit")
    def _valid_favunit(self, proposal):
        favunit = proposal['value']
        if favunit is None and self.value.favunit is None:
            # we fall back on the passed quantity's favunit
            # (that could be None also)
            return self.value._pick_smart_favunit()
        else:
            self.value.favunit = favunit
            return favunit

    @traitlets.validate("qmin")
    def _valid_favunit(self, proposal):
        proposal = quantify(proposal['value']) 
        self.slider.min = proposal.value

    @traitlets.validate("qmax")
    def _valid_favunit(self, proposal):
        proposal = quantify(proposal['value']) 
        self.slider.max = proposal.value


        # qmin must be a quantity
        # must have same dimension
        #if self.dimension 
        #    raise ValueError()
    


class QuantityTextSlider(QuantityText):
    """A QuantitySlider where the value is displayed and can be changed using a QuantityText

    Both widgets are merged in the QuantiyText VBox as children
    We drop the Quantityslider's label
    We drop the QuantityText's description
    """

    def __init__(self, *args, **kwargs):
        # favunit is passed to the QuantityText for display purpose
        favunit = kwargs.pop("favunit", None)
        # but description is kept in the slider
        # description = kwargs.pop("description", "")
        # so we leave an empty description for the QuantityText
        super().__init__(*args, description="", favunit=favunit)

        self.qslider = QuantitySlider(*args,
                                      label=False,
                                      **kwargs)

        # both widgets have a value trait that is a Quantity instance : we want them to be the
        # same at all time : no processing is needed so we use a link
        link = ipyw.link(
            (self, "value"),
            (self.qslider, "value")
        )

        link = ipyw.link(
            (self, "favunit"),
            (self.qslider, "favunit"),
        )

        # set the QuantityText HBox children with just the slider and the text
        self.children = [
            self.qslider,
            self.text,
        ]


class QuantityRangeSlider(ipyw.Box, ipyw.ValueWidget, ipyw.DOMWidget):
    """
    TODO :
     - value_left and value_right are useless, could be done with only value (and should be)

    """
    # dimension trait : a Dimension instance
    dimension = traitlets.Instance(Dimension, allow_none=False)
    # value trait : a Quantity instance
    vale = (traitlets.Instance(Quantity, allow_none=False),
            traitlets.Instance(Quantity, allow_none=False))
    value_left = traitlets.Instance(Quantity, allow_none=False)
    value_right = traitlets.Instance(Quantity, allow_none=False)
    qmin = traitlets.Instance(Quantity, allow_none=False)
    qmax = traitlets.Instance(Quantity, allow_none=False)
    qstep = traitlets.Instance(Quantity, allow_none=False)

    def __init__(self, min=None, max=None, step=None, disabled=False,
                 continuous_update=True, description="Quantity:",
                 fixed_dimension=False, label=True,  # placeholder="Type python expr",
                 favunit=None,
                 **kwargs):
        """
        kwargs are passed to Box.
        """

        super().__init__(**kwargs)

        # quantity work
        # set dimension
        value = quantify(min)
        self.favunit = value.favunit or favunit
        self.dimension = value.dimension
        # if true, any change in value must have same dimension as initial
        # dimension
        self.fixed_dimension = fixed_dimension

        qmin = quantify(min)
        qmax = quantify(max)
        qstep = Quantity(0.1, qmin.dimension)

        # set quantity
        self.value_left = qmin
        self.value_right = qmax

        self.qstep = qstep
        self.qmin = qmin
        self.qmax = qmax
        self.value = self.qmin, self.qmax

        # set text widget
        self.rslider = ipyw.FloatRangeSlider(
            value=[self.value_left.value, self.value_right.value],
            min=self.qmin.value,
            max=self.qmax.value,
            step=self.qstep.value,
            description=description,
            disabled=disabled,
            continuous_update=continuous_update,
            # orientation=orientation,
            readout=False,  # to disable displaying readout value
            # readout_format=readout_format,
            # layout=Layout(width="50%",
            #              margin="0px",
            #              border="solid red"),
        )

        def update_label_on_slider_change(change):
            new_left, new_right = change.new
            self.value_left = Quantity(
                new_left, self.dimension, favunit=self.favunit)
            self.value_right = Quantity(
                new_right, self.dimension, favunit=self.favunit)
            self.value = self.value_left, self.value_right
            self.label.value = str(self.value_left) + \
                "-" + str(self.value_right)
        self.rslider.observe(update_label_on_slider_change, names="value")

        # def update_slider_value(change):
        #    self.slider.value = change.new.value
        # self.observe(update_slider_value, names="value")

        # display the quantity value of the slider in label
        self.label = ipyw.Label(
            value=str(self.value_left) + "-" + str(self.value_right))

        # todo : add callback to update frontend on value change
        def update_slider_value(change):
            self.rslider.value = change.new[0].value, change.new[1].value
        self.observe(update_slider_value, names="value")

        if label:
            self.children = [
                self.rslider,
                self.label,
            ]
        else:
            self.children = [
                self.rslider,
            ]


class FavunitDropdown(ipyw.Box, ipyw.ValueWidget, ipyw.DOMWidget):
    dimension = traitlets.Instance(Dimension)
    value = traitlets.Instance(Quantity, allow_none=True)

    def __init__(self, dimension=None, all_units=False,
                 **kwargs):
        super().__init__(**kwargs)

        self.dimension = dimensionify(dimension)
        self.units = units
        self.units["-"] = Quantity(1, Dimension(None), symbol="-")

        # list of available units
        if self.dimension == Dimension(None) or all_units:
            self.favunit_str_list = [
                u_str for u_str, u_q in self.units.items()]
        else:
            self.favunit_str_list = [
                u_str for u_str,
                u_q in self.units.items() if self.dimension == u_q.dimension]
        self.favunit_str_list.append("-")
        self.value = self.units["-"]

        # dropdown
        self.favunit_dd = ipyw.Dropdown(
            options=self.favunit_str_list,
            # set init value
            value=str(self.value.symbol),
            description='Favunit:',
            layout=Layout(width="30%",
                          margin="5px 5px 5px 5px",
                          border="solid black"),
        )

        self.children = [self.favunit_dd]

        # 3. Change favunit
        # selection of favunit

        def update_favunit_on_favunit_dd_change(change):
            # retrieve new favunit q
            self.value = self.units[change.new]
        self.favunit_dd.observe(
            update_favunit_on_favunit_dd_change, names="value")

        def update_dd_value(change):
            self.favunit_dd.value = str(change.new.symbol)
        self.observe(update_dd_value, names="value")


class QuantityTextWithFavunitDropdown(QuantityText):
    """
    Wraps a QuantitText and a FavunitDropdown
    Remembering that :
        QuantityText has traits :
            - dimension
            - value
            - favunit
        FavunitDropdown :
            - dimension
            - value : the favunit
    So we should be able to link the favunit
    """

    def __init__(self, *args, **kwargs):

        # Create a dropdown widget
        self.ddw = FavunitDropdown()
        super().__init__(*args, **kwargs)

        # Link the favunits
        ipyw.link((self, "favunit"), (self.ddw, "value"))

        # Boxing widgets together
        self.children = [self.text, self.ddw]

    # def update_qfavunit(self, change):
    #    self.favunit = self.ddw.units[change["new"]]
    #    self.value.favunit=self.favunit
    #    self.text.value = str(self.value)


class QuantitySliderDescriptor():

    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def __set_name__(self, owner, name):
        # self.R
        self.public_name = name
        # actually refers to self._R_w
        self.private_name = name + "_w"

    def __set__(self, obj, value):
        # todo : find a way to not creat a new slider at each set
        if hasattr(obj, self.private_name):
            # print("setting value")
            setattr(getattr(obj, self.private_name), "value", value)
        else:
            # print("create new widget")
            setattr(
                obj,
                self.private_name,
                QuantityTextSlider(
                    value,
                    description=self.public_name,
                    min=self.min,
                    max=self.max))

    def __get__(self, obj, objtype=None):
        if hasattr(obj, self.private_name):
            value = getattr(obj, self.private_name).value
            return value
        else:
            setattr(
                obj,
                self.private_name,
                QuantityTextSlider(
                    description=self.public_name,
                    min=self.min,
                    max=self.max))
