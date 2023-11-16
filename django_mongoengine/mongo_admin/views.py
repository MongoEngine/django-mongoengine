from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.views.main import ORDER_VAR, ChangeList
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.paginator import InvalidPage


class DocumentChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pk_attname = self.lookup_opts.pk_name

    def get_results(self, request):
        paginator = self.model_admin.get_paginator(request, self.queryset, self.list_per_page)
        # Get the number of objects, with admin filters applied.
        result_count = paginator.count

        # Get the total number of objects, with no admin filters applied.
        # Perform a slight optimization: Check to see whether any filters were
        # given. If not, use paginator.hits to calculate the number of objects,
        # because we've already done paginator.hits and the value is cached.
        if len(self.queryset._query) == 1:
            full_result_count = result_count
        else:
            full_result_count = self.root_queryset.count()

        can_show_all = result_count <= self.list_max_show_all
        multi_page = result_count > self.list_per_page

        # Get the list of objects to display on this page.
        if (self.show_all and can_show_all) or not multi_page:
            result_list = self.queryset.clone()
        else:
            try:
                result_list = paginator.page(self.page_num).object_list
            except InvalidPage:
                raise IncorrectLookupParameters

        self.result_count = result_count
        self.full_result_count = full_result_count
        self.result_list = result_list
        self.can_show_all = can_show_all
        self.multi_page = multi_page
        self.paginator = paginator

    def _get_default_ordering(self):
        try:
            ordering = super()._get_default_ordering()
        except AttributeError:
            ordering = []
            if self.model_admin.ordering:
                ordering = self.model_admin.ordering
            elif self.lookup_opts.ordering:
                ordering = self.lookup_opts.ordering
        return ordering

    def get_ordering(self, request=None, queryset=None):
        """
        Returns the list of ordering fields for the change list.
        First we check the get_ordering() method in model admin, then we check
        the object's default ordering. Then, any manually-specified ordering
        from the query string overrides anything. Finally, a deterministic
        order is guaranteed by ensuring the primary key is used as the last
        ordering field.
        """
        if queryset is None:
            # with Django < 1.4 get_ordering works without fixes for mongoengine
            return super().get_ordering()

        params = self.params
        ordering = list(self.model_admin.get_ordering(request) or self._get_default_ordering())
        if ORDER_VAR in params:
            # Clear ordering and used params
            ordering = []
            order_params = params[ORDER_VAR].split(".")
            for p in order_params:
                try:
                    none, pfx, idx = p.rpartition("-")
                    field_name = self.list_display[int(idx)]
                    order_field = self.get_ordering_field(field_name)
                    if not order_field:
                        continue  # No 'admin_order_field', skip it
                    ordering.append(pfx + order_field)
                except (IndexError, ValueError):
                    continue  # Invalid ordering specified, skip it.

        # Add the given query's ordering fields, if any.
        try:

            def sign(t):
                return t[1] > 0 and "+" or "-"

            qs_ordering = [sign(t) + t[0] for t in queryset._ordering]
            ordering.extend(qs_ordering)
        except:  # noqa: E722
            pass

        # Ensure that the primary key is systematically present in the list of
        # ordering fields so we can guarantee a deterministic order across all
        # database backends.
        pk_name = self.lookup_opts.pk.name
        if not (set(ordering) & {"pk", "-pk", pk_name, "-" + pk_name}):
            # The two sets do not intersect, meaning the pk isn't present. So
            # we add it.
            ordering.append("pk")
        return ordering

    def get_queryset(self, request=None):
        # First, we collect all the declared list filters.
        qs = self.root_queryset.clone()

        (
            self.filter_specs,
            self.has_filters,
            remaining_lookup_params,
            search_may_have_duplicates,
            has_active_filters,
        ) = self.get_filters(request)

        # Then, we let every list filter modify the queryset to its liking.
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(request, qs)
            if new_qs is not None:
                qs = new_qs

        try:
            # Finally, we apply the remaining lookup parameters from the query
            # string (i.e. those that haven't already been processed by the
            # filters).
            qs = qs.filter(**remaining_lookup_params)
            # TODO: This should probably be mongoengine exceptions
        except (SuspiciousOperation, ImproperlyConfigured):
            # Allow certain types of errors to be re-raised as-is so that the
            # caller can treat them in a special way.
            raise
        except Exception as e:
            # Every other error is caught with a naked except, because we don't
            # have any other way of validating lookup parameters. They might be
            # invalid if the keyword arguments are incorrect, or if the values
            # are not in the correct type, so we might get FieldError,
            # ValueError, ValidationError, or ?.
            raise IncorrectLookupParameters(e)

        # Set ordering.
        ordering = self.get_ordering(request, qs)
        qs = qs.order_by(*ordering)

        # Apply search results
        qs, search_may_have_duplicates = self.model_admin.get_search_results(
            request,
            qs,
            self.query,
        )

        return qs
